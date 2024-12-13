##############################################################################
# Data access layer
#
# Provides a clean, type-safe interface for the rest of the application to 
# interact with the database, abstracting away the details of MongoDB 
# operations and document structure
##############################################################################

# Handles MongoDB's object ID
from bson import ObjectId
from fastapi import HTTPException
# Asynchronous MongoDB driver
from motor.motor_asyncio import AsyncIOMotorCollection
# Specified return behavior and update operations
from pymongo import ReturnDocument
# Create data models with validation
from pydantic import BaseModel

# Generates unique IDs
from uuid import uuid4

##############################################################################
# from_doc static methods create instances from MongoDB documents:
##############################################################################

# Model to represent summary of the to-do list
class ListSummary(BaseModel):
    id: str
    name: str
    item_count: int

    @staticmethod
    def from_doc(doc) -> "ListSummary":
        return ListSummary(
            id=str(doc["_id"]),
            name=doc["name"],
            item_count=doc["item_count"],
        )
    
    
# Individual to-do item
class ToDoListItem(BaseModel):
    id: str
    label: str
    checked: bool

    @staticmethod
    def from_doc(item) -> "ToDoListItem":
        if "id" not in item or "label" not in item or "checked" not in item:
            raise ValueError("Invalid item format")
        return ToDoListItem(
            id=item["id"],
            label=item["label"],
            checked=item["checked"],
        )
    

# Complete to-do list with items
class ToDoList(BaseModel):
    id: str
    name: str
    items: list[ToDoListItem]

    @staticmethod
    def from_doc(doc) -> "ToDoList":
        if "_id" not in doc or "name" not in doc or "items" not in doc:
            raise ValueError("Invalid document format")
        return ToDoList(
            id=str(doc["_id"]),
            name=doc["name"],
            items=[ToDoListItem.from_doc(item) for item in doc["items"]],
        )
    
    
# Encapsulate all database operations
class ToDoDAL:
    def __init__(self, todo_collection: AsyncIOMotorCollection):
        self._todo_collection = todo_collection

    ##########################################################################
    # All methods are asynchronous, using async/await syntax for non-blocking 
    # database operations
    #
    # Extensive use of type hints throughout for better code clarity, IDE 
    # support
    #
    # Data transformation—converts between MongoDB documents, pydantic models
    # for type safety and validation
    #
    # All methods accept an optional session parameter for transaction support
    #
    # Most methods return None if the operation fails or document not found
    ##########################################################################

    async def list_todo_lists(self, session=None):
        """
        Asynchronously yield summaries of all to-do lists from the database.
        """
        async for doc in self._todo_collection.find(
            {},
            projection={
                "name": 1,
                "item_count": {"$size": "$items"},
            },
            sort={"name": 1},
            session=session
        ):
            yield ListSummary.from_doc(doc)

    async def create_todo_list(self, name: str, session=None) -> str:
        """
        Creates a new to-do list and return its ID.
        """
        response = await self._todo_collection.insert_one(
            {"name": name, "items": []},
            session=session,
        )
        return str(response.inserted_id)
    
    async def get_todo_list(
        self,
        id: str | ObjectId,
        session=None,
    ) -> ToDoList:
        """
        Retrieves a specific to-do list.
        """
        doc = await self._todo_collection.find_one(
            {"_id": ObjectId(id)},
            session=session
        )
        # Add a check to handle when no document is found
        if doc is None:
            raise HTTPException(status_code=404, detail="Todo list not found")
        
        return ToDoList.from_doc(doc)
    
    async def delete_todo_list(
        self,
        id: str | ObjectId,
        session=None,
    ) -> bool:
        """
        Delete a specific to-do list.
        """
        response = await self._todo_collection.delete_one(
            {"_id": ObjectId(id)},
            session=session,
        )
        print(f"MongoDB delete response: {response.raw_result}")
        return response.deleted_count == 1
    
    async def create_item(
        self,
        id: str | ObjectId,
        label: str,
        session=None,
    ) -> ToDoList | None:
        """
        Create an item for a to-do list.
        """
        result = await self._todo_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$push": {
                    "items": {
                        "id": uuid4().hex,
                        "label": label,
                        "checked": False,
                    }
                }
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        if result:
            return ToDoList.from_doc(result)
        
    async def set_checked_state(
        self,
        doc_id: str | ObjectId,
        item_id: str,
        checked_state: bool,
        session=None,
    ) -> ToDoList | None:
        """
        Update the checked state of a specific item.
        """
        result = await self._todo_collection.find_one_and_update(
            {"_id": ObjectId(doc_id), "items.id": item_id},
            {"$set": {"items.$.checked": checked_state}},
            session=session,
            return_document = ReturnDocument.AFTER,
        )
        if result:
            return ToDoList.from_doc(result)
        
    async def delete_item(
        self,
        doc_id: str | ObjectId,
        item_id: str,
        session=None,
    ) -> ToDoList | None:
        """
        Delete a specific item in a to-do list.
        """
        result = await self._todo_collection.find_one_and_update(
            {"_id": ObjectId(doc_id)},
            {"$pull": {"items": {"id": item_id}}},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        if result:
            return ToDoList.from_doc(result)