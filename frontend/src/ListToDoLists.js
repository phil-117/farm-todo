import "./ListToDoLists.css";
import { useRef, useState } from "react";
import { BiSolidTrash } from "react-icons/bi";

function ListToDoLists({
    listSummaries,
    handleSelectList,
    handleNewToDoList,
    handleDeleteToDoList,
}) {
    const [inputValue, setInputValue] = useState("");
    const inputRef = useRef(null);
    
    const handleSubmit = () => {
        if (inputValue.trim() === "") {
            inputRef.current.focus();
            return;
        }
        handleNewToDoList(inputValue);
        setInputValue("");
        inputRef.current.focus();
    }

    const handleKeyDown = (e) => {
        if (e.key === "Enter") {
            handleSubmit();
        }
    }

    if (listSummaries === null) {
        return (
            <div className="ListToDoLists loading">
                Loading to-do lists ...
            </div>
        );
    }


    return (
        <div className="ListToDoLists">
            <h1>Home</h1>
            <div className="box">
                <label>
                    New List:&nbsp;
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </label>
                <button
                    onClick={handleSubmit}
                >
                    Submit
                </button>
            </div>
            {listSummaries.length > 0 ? (
                listSummaries.map((summary) => {
                    return (
                        <div
                            key={summary.id}
                            className="summary"
                            onClick={() => handleSelectList(summary.id)}
                        >
                            <span className="name">{summary.name}</span>
                            <span 
                                className="count"
                            >
                                ({summary.item_count} items)
                            </span>
                            <span className="flex"></span>
                            <span
                                className="trash"
                                onClick={(evt) => {
                                    evt.stopPropagation();
                                    handleDeleteToDoList(summary.id);
                                }}
                            >
                                <BiSolidTrash />
                            </span>
                        </div>
                    );
                })
            ) : (
                <div className="box">There are currently no lists.</div>
            )}
        </div>
    );
}

export default ListToDoLists;