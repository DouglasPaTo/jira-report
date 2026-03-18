from fastapi import APIRouter, Request, Depends, HTTPException, responses
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import json
from app.db.session import get_db
from app.db.models import User, UserOrganization, Ticket

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="app/templates")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_default_admin(db):
    existing = db.query(User).filter(User.username == "usrking").first()
    if not existing:
        admin = User(
            username="usrking",
            password_hash=get_password_hash("MortySeiya!"),
            is_admin=1
        )
        db.add(admin)
        db.commit()

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuário ou senha inválidos"
        })
    
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["is_admin"] = user.is_admin
    
    return responses.RedirectResponse(url="/", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return responses.RedirectResponse(url="/login")

@router.get("/usuarios")
async def usuarios_page(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return responses.RedirectResponse(url="/login")
    
    if not request.session.get("is_admin"):
        return responses.RedirectResponse(url="/")
    
    users = db.query(User).all()
    
    all_tickets = db.query(Ticket).all()
    all_orgs = set()
    for t in all_tickets:
        orgs = json.loads(t.organizations) if t.organizations else []
        for org in orgs:
            all_orgs.add(org)
    
    sorted_orgs = sorted(list(all_orgs))
    
    return templates.TemplateResponse("usuarios.html", {
        "request": request,
        "users": users,
        "organizations": sorted_orgs
    })

@router.post("/usuarios/criar")
async def criar_usuario(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id") or not request.session.get("is_admin"):
        return {"error": "Não autorizado"}
    
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    orgs_str = form.get("organizations", "")
    selected_orgs = [o.strip() for o in orgs_str.split(",") if o.strip()]
    
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return {"error": "Usuário já existe"}
    
    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        is_admin=0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    for org in selected_orgs:
        if org == "TODAS":
            user_org = UserOrganization(
                user_id=new_user.id,
                organization="__TODAS__"
            )
            db.add(user_org)
            break
        elif org:
            user_org = UserOrganization(
                user_id=new_user.id,
                organization=org
            )
            db.add(user_org)
    db.commit()
    
    return {"message": f"Usuário {username} criado com sucesso!"}

@router.post("/usuarios/excluir")
async def excluir_usuario(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id") or not request.session.get("is_admin"):
        return {"error": "Não autorizado"}
    
    form = await request.form()
    user_id = form.get("user_id")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if user.username == "usrking":
            return {"error": "Não é possível excluir o admin padrão"}
        db.query(UserOrganization).filter(UserOrganization.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        return {"message": "Usuário excluído"}
    
    return {"error": "Usuário não encontrado"}

@router.post("/usuarios/alterar-senha")
async def alterar_senha(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id") or not request.session.get("is_admin"):
        return {"error": "Não autorizado"}
    
    form = await request.form()
    user_id = form.get("user_id")
    new_password = form.get("new_password")
    
    if not new_password or len(new_password) < 4:
        return {"error": "Senha deve ter pelo menos 4 caracteres"}
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return {"message": "Senha alterada com sucesso!"}
    
    return {"error": "Usuário não encontrado"}

@router.post("/usuarios/criar-admin")
async def criar_admin(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id") or not request.session.get("is_admin"):
        return {"error": "Não autorizado"}
    
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    if not username or not password or len(password) < 4:
        return {"error": "Usuário e senha são obrigatórios (senha mínimo 4 caracteres)"}
    
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return {"error": "Usuário já existe"}
    
    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        is_admin=1
    )
    db.add(new_user)
    db.commit()
    
    return {"message": f"Admin {username} criado com sucesso!"}
