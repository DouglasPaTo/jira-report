from fastapi import APIRouter, Request, Depends, HTTPException, responses, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import json
from app.db.session import get_db
from app.db.models import Ticket, UserOrganization
from app.services.jira_service import fetch_done_tickets, extract_ticket_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.on_event("startup")
def startup_event():
    from app.db.session import engine, Base
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    from app.routers.auth import create_default_admin
    create_default_admin(db)
    db.close()

@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    start_date: str = None,
    end_date: str = None,
    organization: str = None,
    label: str = None,
    assignee: str = None,
    status: str = None,
    project: str = None
):
    try:
        user_id = request.session.get("user_id")
        is_admin = request.session.get("is_admin", 0)
        if not user_id:
            return responses.RedirectResponse(url="/login")
    except:
        return responses.RedirectResponse(url="/login")
    
    user_orgs = []
    has_todas = False
    if not is_admin:
        user_orgs = db.query(UserOrganization).filter(UserOrganization.user_id == user_id).all()
        user_orgs = [uo.organization for uo in user_orgs]
        if "__TODAS__" in user_orgs:
            has_todas = True
            user_orgs = []
    
    all_tickets = db.query(Ticket).all()
    all_orgs = set()
    all_labels = set()
    all_assignees = set()
    all_statuses = set()
    all_projects = set()
    
    for t in all_tickets:
        orgs = json.loads(t.organizations) if t.organizations else []
        lbls = json.loads(t.labels) if t.labels else []
        extra = json.loads(t.extra_fields) if t.extra_fields else {}
        status_obj = extra.get('status', {})
        proj_obj = extra.get('project', {})
        
        if proj_obj:
            proj_name = proj_obj.get('name', proj_obj.get('key', ''))
            if proj_name:
                all_projects.add(proj_name)
        
        if status_obj and status_obj.get('name'):
            all_statuses.add(status_obj['name'])
        if status_obj and status_obj.get('name'):
            all_statuses.add(status_obj['name'])
        
        for org in orgs:
            if is_admin or has_todas or org in user_orgs:
                all_orgs.add(org)
        for lbl in lbls:
            all_labels.add(lbl)
        if t.assignee:
            all_assignees.add(t.assignee)
    
    query = db.query(Ticket)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Ticket.due_date >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Ticket.due_date <= end)
        except:
            pass
    
    if not is_admin and user_orgs and not has_todas:
        org_filters = [Ticket.organizations.like(f'%"{org}"%') for org in user_orgs]
        from sqlalchemy import or_
        query = query.filter(or_(*org_filters))
    
    if organization and organization != "all":
        query = query.filter(Ticket.organizations.like(f'%"{organization}"%'))
    
    if label and label != "all":
        query = query.filter(Ticket.labels.like(f'%"{label}"%'))
    
    if assignee and assignee != "all":
        query = query.filter(Ticket.assignee == assignee)
    
    if status and status != "all":
        query = query.filter(Ticket.extra_fields.like(f'%"name": "{status}"%'))
    
    if project and project != "all":
        query = query.filter(Ticket.extra_fields.like(f'%"name": "{project}"%'))
    
    tickets = query.order_by(Ticket.due_date.desc()).all()
    
    tickets_with_lists = []
    for t in tickets:
        due_date_str = t.due_date.strftime('%Y-%m-%d') if t.due_date else None
        extra = json.loads(t.extra_fields) if t.extra_fields else {}
        status_name = extra.get('status', {}).get('name', '') if extra.get('status') else ''
        tickets_with_lists.append({
            'id': t.id,
            'jira_id': t.jira_id,
            'key': t.key,
            'summary': t.summary,
            'description': t.description,
            'last_comment': t.last_comment,
            'time_spent': t.time_spent,
            'labels': json.loads(t.labels) if t.labels else [],
            'organizations': json.loads(t.organizations) if t.organizations else [],
            'assignee': t.assignee,
            'due_date': due_date_str,
            'status': status_name,
            'extra_fields': extra,
        })
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "tickets": tickets_with_lists,
        "organizations": sorted(list(all_orgs)),
        "labels": sorted(list(all_labels)),
        "assignees": sorted(list(all_assignees)),
        "statuses": sorted(list(all_statuses)),
        "projects": sorted(list(all_projects)),
        "filters": {
            "start_date": start_date or "",
            "end_date": end_date or "",
            "organization": organization or "all",
            "label": label or "all",
            "assignee": assignee or "all",
            "status": status or "all",
            "project": project or "all"
        }
    })

@router.post("/atualizar")
def atualizar_tickets(
    request: Request,
    db: Session = Depends(get_db),
    mode: str = Query("full")
):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"error": "Sessão expirada. Faça login novamente."}
    
    try:
        update_mode = (mode == "quick")
        issues = fetch_done_tickets(update_mode=update_mode)
        saved_count = 0
        
        for issue in issues:
            data = extract_ticket_data(issue)
            
            existing = db.query(Ticket).filter(Ticket.jira_id == data['jira_id']).first()
            
            if existing:
                existing.summary = data['summary']
                existing.description = data['description']
                existing.last_comment = data['last_comment']
                existing.time_spent = data['time_spent']
                existing.labels = data['labels']
                existing.organizations = data['organizations']
                existing.assignee = data['assignee']
                existing.due_date = data['due_date']
                existing.extra_fields = data['extra_fields']
            else:
                ticket = Ticket(**data)
                db.add(ticket)
                saved_count += 1
        
        db.commit()
        
        return {"message": f"Tickets atualizados! {saved_count} novos tickets salvos.", "total": len(issues)}
    except Exception as e:
        return {"error": str(e)}

@router.post("/exportar")
async def exportar_html(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user_id = request.session.get("user_id")
        is_admin = request.session.get("is_admin", 0)
        if not user_id:
            raise HTTPException(status_code=401)
    except:
        raise HTTPException(status_code=401)
    
    form = await request.form()
    start_date = form.get("start_date")
    end_date = form.get("end_date")
    organization = form.get("organization")
    label = form.get("label")
    assignee = form.get("assignee")
    status = form.get("status")
    project = form.get("project")
    
    user_orgs = []
    has_todas = False
    if not is_admin:
        user_orgs = db.query(UserOrganization).filter(UserOrganization.user_id == user_id).all()
        user_orgs = [uo.organization for uo in user_orgs]
        if "__TODAS__" in user_orgs:
            has_todas = True
            user_orgs = []
    
    query = db.query(Ticket)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Ticket.due_date >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Ticket.due_date <= end)
        except:
            pass
    
    if project and project != "all":
        query = query.filter(Ticket.extra_fields.like(f'%"name": "{project}"%'))
    
    if not is_admin and user_orgs and not has_todas:
        org_filters = [Ticket.organizations.like(f'%"{org}"%') for org in user_orgs]
        from sqlalchemy import or_
        query = query.filter(or_(*org_filters))
    
    if organization and organization != "all":
        query = query.filter(Ticket.organizations.like(f'%"{organization}"%'))
    
    if label and label != "all":
        query = query.filter(Ticket.labels.like(f'%"{label}"%'))
    
    if assignee and assignee != "all":
        query = query.filter(Ticket.assignee == assignee)
    
    tickets = query.order_by(Ticket.due_date.asc()).all()
    
    tickets_with_lists = []
    label_times = {}
    label_counts = {}
    total_minutes = 0
    
    for t in tickets:
        labels = json.loads(t.labels) if t.labels else []
        
        minutes = 0
        if t.time_spent:
            import re
            ts = t.time_spent.strip().lower()
            total_minutes_calc = 0
            
            day_match = re.search(r'(\d+)\s*day', ts)
            if day_match:
                total_minutes_calc += int(day_match.group(1)) * 24 * 60
            
            hour_match = re.search(r'(\d+)\s*hour', ts)
            if hour_match:
                total_minutes_calc += int(hour_match.group(1)) * 60
            
            min_match = re.search(r'(\d+)\s*minute', ts)
            if min_match:
                total_minutes_calc += int(min_match.group(1))
            
            if total_minutes_calc == 0:
                match = re.match(r'(?:(\d+)h)?\s*(?:(\d+)m)?', ts)
                if match:
                    hours = int(match.group(1)) if match.group(1) else 0
                    mins = int(match.group(2)) if match.group(2) else 0
                    total_minutes_calc = hours * 60 + mins
                elif ':' in ts:
                    match = re.match(r'(\d+):(\d+)', ts)
                    if match:
                        hours = int(match.group(1))
                        mins = int(match.group(2))
                        total_minutes_calc = hours * 60 + mins
                elif ts.isdigit():
                    total_minutes_calc = int(ts)
            
            minutes = total_minutes_calc
        
        for lbl in labels:
            if lbl not in label_times:
                label_times[lbl] = 0
                label_counts[lbl] = 0
            label_times[lbl] += minutes
            label_counts[lbl] += 1
        
        total_minutes += minutes
        
        tickets_with_lists.append({
            'key': t.key,
            'summary': t.summary,
            'description': t.description,
            'last_comment': t.last_comment,
            'time_spent': t.time_spent,
            'labels': labels,
            'assignee': t.assignee,
            'due_date': t.due_date,
        })
    
    def format_time(minutes):
        hours = minutes // 60
        mins = minutes % 60
        if hours and mins:
            return f"{hours}h {mins}m"
        elif hours:
            return f"{hours}h"
        else:
            return f"{mins}m"
    
    logo_base64 = ""
    import base64
    import os
    logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
    
    org_name = organization if organization and organization != "all" else "Todas"
    
    label_times_sorted = sorted(label_times.items(), key=lambda x: x[1], reverse=True)
    mins_formatted = {label: format_time(mins) for label, mins in label_times_sorted}
    label_percentages = {label: round(mins / total_minutes * 100, 1) for label, mins in label_times_sorted} if total_minutes > 0 else {}
    label_counts_sorted = {label: label_counts[label] for label, mins in label_times_sorted}
    
    tickets_for_template = []
    for t in tickets_with_lists:
        tickets_for_template.append({
            'key': t['key'],
            'summary': t['summary'],
            'description': t['description'],
            'last_comment': t['last_comment'],
            'time_spent': t['time_spent'],
            'labels': t['labels'],
            'assignee': t['assignee'],
            'due_date_formatted': t['due_date'].strftime('%d/%m/%Y') if t['due_date'] else '-',
        })
    
    def format_date(date_str):
        if not date_str:
            return '-'
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return date_str
    
    context = {
        'logo_base64': logo_base64,
        'org_name': org_name,
        'start_date': format_date(start_date),
        'end_date': format_date(end_date),
        'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'total_tickets': len(tickets_with_lists),
        'total_time_formatted': format_time(total_minutes),
        'label_times_sorted': label_times_sorted,
        'mins_formatted': mins_formatted,
        'label_percentages': label_percentages,
        'label_counts': label_counts_sorted,
        'tickets': tickets_for_template,
        'is_admin': is_admin,
    }
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    from fastapi.responses import HTMLResponse
    return templates.TemplateResponse("report.html", {"request": request, **context})
