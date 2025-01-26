import logging

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

logging.basicConfig(level=logging.DEBUG)
class Term(SQLModel, table=True):
    term: str = Field(primary_key=True)
    description: str | None = Field(default=None)

class TermRelation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    term_from: str = Field(foreign_key="term.term")
    term_to: str = Field(foreign_key="term.term")
    label: str = Field(default="")

sqlite_file_name = "glossary.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/glossary/")
def create_term(term: Term, session: SessionDep) -> Term:
    session.add(term)
    session.commit()
    session.refresh(term)
    return term

@app.post("/search", response_class=HTMLResponse)
def search_term_page(request: Request, session: SessionDep, term: str = Form(...)):
    db_term = session.get(Term, term)
    if not db_term:
        if not db_term:
            return templates.TemplateResponse("search_results.html", {
                "request": request,
                "message": f"Term '{term}' not found."
            })
    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "term": db_term.term,
        "description": db_term.description or "No description available",
        "edit_url": f"/edit/{db_term.term}",
        "delete_url": f"/glossary/{db_term.term}"
    })


@app.delete("/glossary/{term}")
def delete_term(term: str, session: SessionDep):
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    session.delete(db_term)
    session.commit()
    return {"ok": True}


# Фронтенд маршруты
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request,
               session: SessionDep,
               offset: int = 0,
               limit: Annotated[int, Query(le=100)] = 100,
               ):
    terms = session.exec(select(Term).offset(offset).limit(limit)).all()
    return templates.TemplateResponse("terms.html", {"request": request, "terms": terms})


@app.get("/edit/{term}", response_class=HTMLResponse)
def edit_page(request: Request, term: str, session: SessionDep):
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    return templates.TemplateResponse("edit.html", {"request": request, "term": db_term})


@app.put("/glossary/{term}")
async def update_term(term: str, request: Request, session: SessionDep) -> Term:
    data = await request.json()  # Получение данных в формате JSON
    description = data.get("description")
    if not description:
        raise HTTPException(status_code=400, detail="Description is required")

    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    db_term.description = description
    session.add(db_term)
    session.commit()
    session.refresh(db_term)
    return db_term


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})


@app.get("/graph", response_class=HTMLResponse)
def graph_page(request: Request, session: SessionDep):
    terms = session.exec(select(Term)).all()
    relations = session.exec(select(TermRelation)).all()

    nodes = [{"id": term.term, "label": term.term} for term in terms]
    edges = [{"from": relation.term_from, "to": relation.term_to,
              "label": relation.label} for relation in relations]

    # Отладочный вывод
    print("Nodes:", nodes)
    print("Edges:", edges)

    return templates.TemplateResponse("graph.html", {
        "request": request,
        "nodes": nodes,
        "edges": edges
    })


@app.post("/add_relation")
def add_relation(
    term_from: str = Body(...),
    term_to: str = Body(...),
    label: str = Body(...),
    session: Session = Depends(get_session)
):
    # Проверка существования терминов
    term1 = session.get(Term, term_from)
    term2 = session.get(Term, term_to)
    if not term1 or not term2:
        raise HTTPException(status_code=404, detail="One or both terms not found")

    relation = TermRelation(term_from=term_from, term_to=term_to, label=label)
    session.add(relation)
    session.commit()
    return {"ok": True}

@app.get("/add_relation", response_class=HTMLResponse)
def add_relation_page(request: Request, session: SessionDep):
    # Извлекаем все термины
    terms = session.exec(select(Term)).all()
    return templates.TemplateResponse("add_relation.html", {
        "request": request,
        "terms": terms
    })

def add_base_data(session: Session):
    # Проверяем, есть ли уже данные в базе
    existing_terms = session.exec(select(Term)).all()
    if existing_terms:
        logging.debug("База данных уже содержит данные. Пропуск добавления тестовых данных.")
        return

    # Создаем тестовые термины
    terms_data = [
        {"term": "Микросервис", "description": "Независимо развертываемый сервис, выполняющий одну бизнес-функцию"},
        {"term": "Гранулярность", "description": "Уровень детализации или размер микросервиса"},
        {"term": "Монолит", "description": "Единое приложение, где все компоненты tightly coupled"},
        {"term": "Слабая связанность", "description": "Принцип, при котором компоненты минимально зависят друг от друга"},
        {"term": "API Gateway", "description": "Единая точка входа для клиентов, которая маршрутизирует запросы к микросервисам"},
        {"term": "Event-Driven Architecture", "description": "Архитектура, основанная на событиях и асинхронной коммуникации"},
        {"term": "Docker", "description": "Платформа для контейнеризации приложений"},
        {"term": "Kubernetes", "description": "Оркестратор контейнеров для управления микросервисами"},
        {"term": "Реестр сервисов", "description": "База данных, которая хранит информацию о доступных микросервисах"},
        {"term": "Масштабируемость", "description": "Способность системы обрабатывать увеличение нагрузки"},
    ]

    # Добавляем термины в базу данных
    for term_data in terms_data:
        term = Term(**term_data)
        session.add(term)
    session.commit()

    # Создаем тестовые связи
    relations_data = [
        {"term_from": "Микросервис", "term_to": "Гранулярность", "label": "определяется"},
        {"term_from": "Микросервис", "term_to": "Слабая связанность", "label": "основан на"},
        {"term_from": "Микросервис", "term_to": "Монолит", "label": "альтернатива"},
        {"term_from": "API Gateway", "term_to": "Микросервис", "label": "управляет запросами к"},
        {"term_from": "Event-Driven Architecture", "term_to": "Микросервис", "label": "используется для коммуникации между"},
        {"term_from": "Docker", "term_to": "Микросервис", "label": "используется для контейнеризации"},
        {"term_from": "Kubernetes", "term_to": "Микросервис", "label": "управляет развертыванием"},
        {"term_from": "Реестр сервисов", "term_to": "Микросервис", "label": "хранит информацию о"},
        {"term_from": "Масштабируемость", "term_to": "Микросервис", "label": "улучшается за счет"},
    ]

    # Добавляем связи в базу данных
    for relation_data in relations_data:
        relation = TermRelation(**relation_data)
        session.add(relation)
    session.commit()

    logging.debug("Тестовые данные успешно добавлены в базу данных.")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    with Session(engine) as session:
        add_base_data(session)