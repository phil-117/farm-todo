import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import ListToDoLists from "./ListToDoLists"
import ToDoList from "./ToDoList"

function App() {
  const [listSummaries, setListSummaries] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);


  useEffect(() => {
    const loadData = async () => {
      try {
        await reloadData();
      } catch (error) {
        alert("There was a problem loading the data.  Please try again later.")
      }
    }
    loadData();
  }, []);

  async function reloadData() {
    const response = await axios.get("/api/lists");
    const data = await response.data;
    setListSummaries(data);
  }


  function handleNewToDoList(newName) {
    const updateData = async () => {
      try {
        const newListData = {name: newName};
        await axios.post(`/api/lists`, newListData)
        await reloadData()
      } catch (error) {
          console.error('List creation failed:', error.response ? error.response.data : error.message);
      }
    };
    updateData();
  }

  async function handleDeleteToDoList(id) {
    try {
        await axios.delete(`/api/lists/${id}`);
        await reloadData();
        return true;
    } catch (error) {
        return false;
    }
  }

  function handleSelectList(id) {
    setSelectedItem(id);
  }

  function backToList() {
    setSelectedItem(null);
    reloadData();
  }


  if (selectedItem === null) {
    return (
      <div className="App">
        <ListToDoLists
          listSummaries={listSummaries}
          handleSelectList={handleSelectList}
          handleNewToDoList={handleNewToDoList}
          handleDeleteToDoList={handleDeleteToDoList}
        />
      </div>
    );
  } else {
    return (
      <div className="App">
        <ToDoList listId={selectedItem} handleBackButton={backToList} />
      </div>
    );
  }
}

export default App;