from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys

from bson import ObjectId
from fastapi import FastAPI, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import uvicorn

from dal import ToDoDAL, ListSummary, ToDoList

# Configure variables for the MongoDB connection and debug mode
COLLECTION_NAME = "todo_lists"
# MongoDB connection string
# Creates an environment with that connection later
MONGODB_URI = os.environ["MONGODB_URI"]
DEBUG = os.environ.get("DEBUG", "").strip().lower() in {
    "1",
    "true",
    "on",
    "yes",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of the FastAPI application.
    """
    # Startup
    client = AsyncIOMotorClient(MONGODB_URI)
    database = client.get_default_database()

    # Ensure the database in available
    pong = await database.command("ping")
    if int(pong["ok"]) != 1:
        raise Exception("Cluster connection is not ok!")

    todo_lists = database.get_collection(COLLECTION_NAME)
    app.todo_dal = ToDoDAL(todo_lists)

    # Yield back to FastAPI application:
    yield

    # Shutdown
    client.close()


app = FastAPI(lifespan=lifespan, debug=DEBUG)


##############################################################################
# API endpoints
##############################################################################

@app.get("/api/lists")
async def get_all_lists() -> list[ListSummary]:
    """
    Retrieve all the to-do lists.
    """
    return [i async for i in app.todo_dal.list_todo_lists()]


class NewList(BaseModel):
    name: str

class NewListResponse(BaseModel):
    id: str
    name: str

@app.post("/api/lists", status_code=status.HTTP_201_CREATED)
async def create_todo_list(new_list: NewList) -> NewListResponse:
    """
    Create a new to-do list.
    """
    return NewListResponse(
        id=await app.todo_dal.create_todo_list(new_list.name),
        name=new_list.name,
    )

@app.get("/api/lists/{list_id}")
async def get_list(list_id: str) -> ToDoList:
    """
    Get a single to-do list.
    """
    return await app.todo_dal.get_todo_list(list_id)

@app.delete("/api/lists/{list_id}")
async def delete_list(list_id: str) -> bool:
    """
    Delete a list.
    """
    return await app.todo_dal.delete_todo_list(list_id)


class NewItem(BaseModel):
    label: str

class NewItemResponse(BaseModel):
    id: str
    label: str

@app.post(
    "/api/lists/{list_id}/items/",
    status_code=status.HTTP_201_CREATED,
    response_model=ToDoList,
)
async def create_new_item(list_id: str, new_item: NewItem) -> ToDoList:
    """
    Create a new item in a list.
    """
    return await app.todo_dal.create_item(list_id, new_item.label)

@app.delete("/api/lists/{list_id}/items/{item_id}")
async def delete_item(list_id: str, item_id: str) -> ToDoList:
    """
    Delete an item in a list.
    """
    return await app.todo_dal.delete_item(list_id, item_id)


class ToDoItemUpdate(BaseModel):
    item_id: str
    checked_state: bool

@app.patch("/api/lists/{list_id}/checked_state")
async def set_checked_state(
    list_id: str,
    update: ToDoItemUpdate,
) -> ToDoList:
    """
    Check that an item has been completed.
    """
    return await app.todo_dal.set_checked_state(
        list_id, update.item_id, update.checked_state
    )


class DummyResponse(BaseModel):
    id: str
    when: datetime

@app.get("/api/dummy")
async def get_dummy() -> DummyResponse:
    """
    Dummy for testing.
    """
    return DummyResponse(
        id=str(ObjectId()),
        when=datetime.now()
    )


def main(argv=sys.argv[1:]):
    """
    Runs the FastAPI application using uvicorn when script executed directly.
    """
    try:
        uvicorn.run("server:app", host="0.0.0.0", port=3001, reload=DEBUG)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

# Pydantic models define the structure of request and response data
# All endpoint handlers are asynchronous
# Status codes set for certain endpoints 