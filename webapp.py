# webapp.py — read-only FastAPI viewer over people/properties/contracts.
#
# Usage:
#     uvicorn webapp:app --reload                       (demo database)
#     CONTRACTER_DB=contracter.db uvicorn webapp:app --reload   (real data)

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import db
import main as contract_main

app = FastAPI(title="Locadora Viewer")
templates = Jinja2Templates(directory=str(contract_main.ROOT / "webapp_templates"))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {
        "db_path":          str(db.DB_PATH),
        "people_count":     len(db.list_people()),
        "properties_count": len(db.list_properties()),
        "contracts_count":  len(db.list_contracts()),
    })


@app.get("/people", response_class=HTMLResponse)
def people_list(request: Request):
    return templates.TemplateResponse(request, "people_list.html", {
        "people": db.list_people(),
    })


@app.get("/people/{person_id}", response_class=HTMLResponse)
def person_detail(request: Request, person_id: int):
    person = db.get_person(person_id)
    if person is None:
        raise HTTPException(404, f"Person {person_id} not found")
    return templates.TemplateResponse(request, "person_detail.html", {
        "person": person,
    })


@app.get("/properties", response_class=HTMLResponse)
def properties_list(request: Request):
    return templates.TemplateResponse(request, "properties_list.html", {
        "properties": db.list_properties(),
    })


@app.get("/properties/{property_id}", response_class=HTMLResponse)
def property_detail(request: Request, property_id: int):
    prop = db.get_property(property_id)
    if prop is None:
        raise HTTPException(404, f"Property {property_id} not found")
    return templates.TemplateResponse(request, "property_detail.html", {
        "property": prop,
    })


@app.get("/contracts", response_class=HTMLResponse)
def contracts_list(request: Request):
    return templates.TemplateResponse(request, "contracts_list.html", {
        "contracts": db.list_contracts(),
    })


@app.get("/contracts/{contract_id}", response_class=HTMLResponse)
def contract_detail(request: Request, contract_id: int):
    contract = db.get_contract(contract_id)
    if contract is None:
        raise HTTPException(404, f"Contract {contract_id} not found")
    return templates.TemplateResponse(request, "contract_detail.html", {
        "contract_id": contract_id,
        "contract":    contract,
    })


@app.get("/contracts/{contract_id}/render", response_class=HTMLResponse)
def contract_render(contract_id: int, mode: str = "preview"):
    """
    Render the full contract exactly as main.py's CLI would — same
    prepare_contract()/render_contract_html() calls, so the web viewer can
    never show something different from what actually gets signed.
    """
    data = db.get_contract(contract_id)
    if data is None:
        raise HTTPException(404, f"Contract {contract_id} not found")
    try:
        contract_type, warnings, errors = contract_main.prepare_contract(
            data, f"db{contract_id}"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    if errors:
        raise HTTPException(422, "; ".join(errors))
    html = contract_main.render_contract_html(
        data, contract_type, review_mode=(mode == "review")
    )
    return HTMLResponse(html)
