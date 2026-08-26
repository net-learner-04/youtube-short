import logging
from urllib.parse import unquote
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


logging.basicConfig(filename="landing.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/go", response_class=HTMLResponse)
def go(request: Request, id: str = None, kw: str = None, target: str = None):
    """뉴스ID/키워드/제휴링크를 받아 인터스티셜 랜딩페이지를 보여주는 라우트"""
    if not target:
        logging.warning(f"target 파라미터 누락 (id={id})")
        raise HTTPException(status_code=400, detail="target 파라미터가 필요합니다")

    target_url = unquote(target)

    if not target_url.startswith("https://"):
        logging.warning(f"비정상 target URL 차단: {target_url}")
        raise HTTPException(status_code=400, detail="유효하지 않은 target URL")

    logging.info(f"[{id}] '{kw}' 랜딩페이지 접속 -> {target_url}")

    return templates.TemplateResponse("redirect.html", {
        "request": request,
        "keyword": kw,
        "target_url": target_url
    })


@app.get("/health")
def health():
    """서버 생존 확인용 헬스체크 라우트"""
    return {"status": "ok"}