from fastapi import APIRouter

main_router = APIRouter()

@main_router.get("/")
def test_route():
    return {"message": "Main router is working!"}
