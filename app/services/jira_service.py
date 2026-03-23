import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import re
import base64
from app.config.settings import settings

BATCH_SIZE = 50

def get_jira_auth():
    return HTTPBasicAuth(settings.jira_email, settings.jira_api_token)


def download_image_as_base64(url, session):
    """Baixa imagem do Jira e converte para base64."""
    try:
        r = session.get(url, timeout=15)
        if r.ok:
            content_type = r.headers.get('Content-Type', 'image/png')
            b64 = base64.b64encode(r.content).decode('utf-8')
            return f"data:{content_type};base64,{b64}"
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")
    return None


def embed_attachment_images(html_content, attachments, session):
    """Adiciona imagens dos attachments no HTML se não houver imagens inline."""
    if not html_content or '<img' in html_content:
        return html_content
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
    image_attachments = [
        att for att in attachments 
        if any(att.get('filename', '').lower().endswith(ext) for ext in image_extensions)
    ]
    
    if not image_attachments:
        return html_content
    
    images_html = '<br/><hr/><p><strong>Imagens anexadas:</strong></p>'
    for att in image_attachments:
        download_url = att.get('content', '')
        if download_url:
            b64_img = download_image_as_base64(download_url, session)
            if b64_img:
                images_html += f'<img src="{b64_img}" alt="{att.get("filename", "imagem")}" style="max-width: 100%; max-height: 600px; width: auto; height: auto; border-radius: 4px; margin: 8px 0;"/><br/>'
    
    return html_content + images_html


def embed_images_in_html(html_content, session):
    """Substitui URLs de imagens do Jira por imagens base64 inline."""
    if not html_content:
        return html_content
    
    attachment_pattern = r'src="(https?://[^"]*atlassian\.net[^"]*attachment[^"]*)"'
    
    def replace_image(match):
        url = match.group(1)
        b64_image = download_image_as_base64(url, session)
        if b64_image:
            return f'src="{b64_image}"'
        return match.group(0)
    
    result = re.sub(attachment_pattern, replace_image, html_content)
    return result


def parse_adf_to_html(adf_obj, session=None, attachments=None, debug_key=None):
    """Converte Atlassian Document Format (ADP) para HTML simples."""
    if not adf_obj or not adf_obj.get('content'):
        return ""
    
    html_parts = []
    
    if debug_key == 'SUP-311':
        print(f"  [DEBUG ADF] Processando ADF com {len(adf_obj.get('content', []))} blocks")
    
    image_attachments = []
    if attachments:
        image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
        for att in attachments:
            filename = att.get('filename', '').lower()
            if any(filename.endswith(ext) for ext in image_exts):
                image_attachments.append(att)
    
    media_index = [0]
    
    def download_attachment(att):
        """Baixa attachment e retorna como base64."""
        if not session or not att:
            return None
        
        download_url = att.get('content', '')
        if not download_url:
            return None
        
        try:
            download_session = requests.Session()
            download_session.auth = session.auth
            download_session.headers.update({
                "Accept": "application/json",
                "X-Atlassian-Token": "no-check"
            })
            r = download_session.get(download_url, timeout=15)
            if r.ok:
                content_type = r.headers.get('Content-Type', 'image/png')
                b64 = base64.b64encode(r.content).decode('utf-8')
                return f"data:{content_type};base64,{b64}"
        except Exception as e:
            print(f"Erro ao baixar attachment {att_id}: {e}")
        return None
    
    def process_inline(inline_content):
        """Processa conteúdo inline (texto, imagens, links)."""
        result = ""
        for item in inline_content:
            item_type = item.get('type')
            
            if item_type == 'text':
                text = item.get('text', '')
                marks = item.get('marks', [])
                for mark in marks:
                    if mark.get('type') == 'strong':
                        text = f"<strong>{text}</strong>"
                    elif mark.get('type') == 'em':
                        text = f"<em>{text}</em>"
                    elif mark.get('type') == 'code':
                        text = f"<code>{text}</code>"
                    elif mark.get('type') == 'link':
                        href = mark.get('attrs', {}).get('href', '#')
                        text = f'<a href="{href}" target="_blank">{text}</a>'
                result += text
                
            elif item_type == 'hardBreak':
                result += '<br/>'
                
            elif item_type == 'emoji':
                short_name = item.get('attrs', {}).get('shortName', '')
                result += f" :{short_name}: "
                
            elif item_type == 'inlineCard':
                attrs = item.get('attrs', {})
                url = attrs.get('url', '')
                text = attrs.get('text', url)
                result += f'<a href="{url}" target="_blank">{text}</a>'
                
        return result
    
    for block in adf_obj['content']:
        block_type = block.get('type')
        
        if block_type == 'paragraph':
            content = block.get('content', [])
            if content:
                html_parts.append(f"<p>{process_inline(content)}</p>")
            else:
                html_parts.append("<p></p>")
        
        elif block_type == 'mediaSingle':
            if media_index[0] < len(image_attachments):
                att = image_attachments[media_index[0]]
                media_index[0] += 1
                b64_img = download_attachment(att)
                if b64_img:
                    width = block.get('attrs', {}).get('width', 400)
                    width_attr = min(width, 600)
                    html_parts.append(f'<img src="{b64_img}" alt="imagem" style="max-width: 100%; max-height: 600px; width: auto; height: auto; border-radius: 4px; margin: 8px 0;"/>')
                else:
                    html_parts.append('<span style="color: #999;">[Imagem não disponível]</span>')
        
        elif block_type == 'mediaGroup':
            for media_item in block.get('content', []):
                if media_item.get('type') == 'media' and media_index[0] < len(image_attachments):
                    att = image_attachments[media_index[0]]
                    media_index[0] += 1
                    b64_img = download_attachment(att)
                    if b64_img:
                        html_parts.append(f'<img src="{b64_img}" alt="imagem" style="max-width: 100%; max-height: 600px; width: auto; height: auto; border-radius: 4px; margin: 8px 0;"/>')
                
        elif block_type == 'heading':
            level = block.get('attrs', {}).get('level', 1)
            content = block.get('content', [])
            text = process_inline(content)
            html_parts.append(f"<h{level}>{text}</h{level}>")
            
        elif block_type == 'bulletList':
            items_html = []
            for item in block.get('content', []):
                item_content = item.get('content', [])
                for p in item_content:
                    if p.get('type') == 'paragraph':
                        items_html.append(f"<li>{process_inline(p.get('content', []))}</li>")
            if items_html:
                html_parts.append(f"<ul>{''.join(items_html)}</ul>")
                
        elif block_type == 'orderedList':
            items_html = []
            for item in block.get('content', []):
                item_content = item.get('content', [])
                for p in item_content:
                    if p.get('type') == 'paragraph':
                        items_html.append(f"<li>{process_inline(p.get('content', []))}</li>")
            if items_html:
                html_parts.append(f"<ol>{''.join(items_html)}</ol>")
                
        elif block_type == 'codeBlock':
            language = block.get('attrs', {}).get('language', '')
            content = block.get('content', [])
            text = process_inline(content)
            html_parts.append(f'<pre><code class="language-{language}">{text}</code></pre>')
            
        elif block_type == 'blockquote':
            content = block.get('content', [])
            inner_html = ""
            for p in content:
                if p.get('type') == 'paragraph':
                    inner_html += f"<p>{process_inline(p.get('content', []))}</p>"
            html_parts.append(f"<blockquote>{inner_html}</blockquote>")
            
        elif block_type == 'rule':
            html_parts.append("<hr/>")
    
    return '\n'.join(html_parts)


def fetch_rendered_content(content_id, content_type, session):
    """Busca conteúdo renderizado (HTML) do Jira via API."""
    try:
        url = f"{settings.jira_url}/rest/api/3/renderedContent"
        params = {"contentId": content_id, "contentType": content_type}
        r = session.get(url, params=params, timeout=15)
        if r.ok:
            return r.text
    except Exception as e:
        print(f"Erro ao buscar renderedContent: {e}")
    return None


def build_jql(project=None):
    jql_parts = []
    
    if project:
        jql_parts.append(f"project = {project}")
    else:
        jql_parts.append("project = SUP")
    
    if settings.jira_status_filter:
        jql_parts.append(f"statusCategory = {settings.jira_status_filter}")
    
    return " AND ".join(jql_parts)


def fetch_done_tickets(update_mode=False):
    session = requests.Session()
    session.auth = get_jira_auth()
    session.headers.update({"Accept": "application/json"})
    
    search_url = f"{settings.jira_url}/rest/api/3/search/jql"
    
    max_tickets = 100 if update_mode else None
    
    base_jql = build_jql()
    
    if max_tickets:
        params = {
            "jql": base_jql,
            "maxResults": max_tickets,
            "fields": "key"
        }
    else:
        params = {
            "jql": base_jql,
            "maxResults": 5000,
            "fields": "key"
        }
    
    r = session.get(search_url, params=params, timeout=30)
    issues = r.json().get("issues", [])
    keys = [i.get("key") for i in issues]
    
    fields_to_fetch = "*all,comment.renderedBody,renderedBody,attachment"
    
    all_issues = []
    for i in range(0, len(keys), BATCH_SIZE):
        batch_keys = keys[i:i+BATCH_SIZE]
        jql = f'key IN ("' + '","'.join(batch_keys) + '")'
        
        params = {"jql": jql, "maxResults": BATCH_SIZE, "fields": fields_to_fetch}
        r = session.get(search_url, params=params, timeout=30)
        batch_issues = r.json().get("issues", [])
        all_issues.extend(batch_issues)
    
    return all_issues


def extract_ticket_data(issue):
    session = requests.Session()
    session.auth = get_jira_auth()
    session.headers.update({"Accept": "application/json"})
    
    fields = issue.get('fields', {})
    
    attachments = fields.get('attachment', [])
    
    print(f"\n=== DEBUG: Ticket {issue.get('key')} ===")
    print(f"Attachments count: {len(attachments)}")
    if len(attachments) > 0 and issue.get('key') == 'SUP-311':
        print(f"  [DEBUG] O ticket SUP-311 tem {len(attachments)} attachments!")
        print(f"  [DEBUG] Description ADF será processado...")
    
    rendered_desc = fields.get('renderedBody', '')
    if rendered_desc:
        desc_html = embed_images_in_html(rendered_desc, session)
    else:
        desc_obj = fields.get('description', {})
        desc_html = parse_adf_to_html(desc_obj, session, attachments, issue.get('key'))
    
    # DESABILITADO: agora parse_adf_to_html já embut as imagens
    # desc_html = embed_attachment_images(desc_html, attachments, session)
    
    # TEMPORÁRIO: desabilitado para debug
    # last_comment_html = embed_attachment_images(last_comment_html, attachments, session)
    
    comment_data = fields.get('comment', {})
    last_comment_html = ""
    
    if isinstance(comment_data, dict):
        comments = comment_data.get('comments', [])
        if comments:
            last_comment = comments[-1]
            
            if issue.get('key') == 'SUP-311':
                print(f"  [DEBUG COMMENT] Keys: {list(last_comment.keys())}")
                body = last_comment.get('body', {})
                print(f"  [DEBUG COMMENT] Body type: {type(body)}")
                if isinstance(body, dict):
                    print(f"  [DEBUG COMMENT] Body ADF: {json.dumps(body)[:400]}...")
            
            rendered = last_comment.get('renderedBody', '')
            if rendered:
                last_comment_html = embed_images_in_html(rendered, session)
            else:
                last_comment_body = last_comment.get('body', {})
                if isinstance(last_comment_body, str):
                    last_comment_html = last_comment_body
                elif isinstance(last_comment_body, dict) and last_comment_body.get('type') == 'doc':
                    last_comment_html = parse_adf_to_html(last_comment_body, session, attachments, issue.get('key'))
                else:
                    print(f"  [DEBUG] last_comment_body tipo: {type(last_comment_body)}")
                    last_comment_html = str(last_comment_body)
    
    # DESABILITADO: causava duplicação
    # last_comment_html = embed_attachment_images(last_comment_html, attachments, session)
    
    timespent = fields.get('timespent')
    time_spent_formatted = ""
    if timespent:
        hours = timespent // 3600
        minutes = (timespent % 3600) // 60
        time_spent_formatted = f"{hours}h {minutes}m" if hours else f"{minutes}m"
    
    labels = fields.get('labels', [])
    
    orgs = fields.get('customfield_10002', [])
    organizations = []
    if orgs:
        organizations = [org.get('name', '') for org in orgs]
    
    assignee = fields.get('assignee', {})
    assignee_name = assignee.get('displayName', '') if assignee else ''
    
    due_date_str = fields.get('duedate', '')
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except:
            pass
    
    return {
        'jira_id': str(issue.get('id')),
        'key': issue.get('key'),
        'summary': fields.get('summary', ''),
        'description': desc_html,
        'last_comment': last_comment_html,
        'time_spent': time_spent_formatted,
        'labels': json.dumps(labels),
        'organizations': json.dumps(organizations),
        'assignee': assignee_name,
        'due_date': due_date,
        'extra_fields': json.dumps(fields),
    }
