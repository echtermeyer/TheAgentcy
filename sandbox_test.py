import time
from src.instantiate import PythonSandbox, FrontendSandbox, DatabaseSandbox
from src.logger import Logger


sandbox_database = DatabaseSandbox()
sandbox_backend = PythonSandbox()
sandbox_frontend= FrontendSandbox()

# test_container = PythonSandbox("test", "testy", "test:latest")

startup_logger = Logger()

backend_string = """
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncpg
from pydantic import BaseModel

app = FastAPI()

# Database connection string
DB_CONNECTION_STRING = "postgresql://user:admin@database:5432"

# Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class Item(BaseModel):
    name: str


async def get_db_connection():
    return await asyncpg.connect(DB_CONNECTION_STRING)

@app.on_event("startup")
async def startup():
    # Create database table on startup
    conn = await get_db_connection()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
    ''')

    # Insert sample data
    sample_items = ['Item 1', 'Item 2', 'Item 3']
    for item in sample_items:
        await conn.execute('''
            INSERT INTO items (name) VALUES ($1)
        ''', item)

    await conn.close()

@app.post("/add_item/")
async def add_item(item: Item):
    conn = await get_db_connection()
    result = await conn.execute('''
        INSERT INTO items(name) VALUES($1) RETURNING id
    ''', item.name)
    await conn.close()
    return {"id": result}

@app.get("/get_items/")
async def get_items():
    conn = await get_db_connection()
    items = await conn.fetch('SELECT * FROM items')
    await conn.close()
    return {"items": items}

@app.delete("/delete_item/{item_id}")
async def delete_item(item_id: int):
    conn = await get_db_connection()
    await conn.execute('''
        DELETE FROM items WHERE id = $1
    ''', item_id)
    await conn.close()
    return {"message": "Item deleted"}

@app.get("/test")
async def read_root():
    await delete_item(1)
    return {"message": "Backend running!"}

# Start the web server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""



frontend_string = """
<!DOCTYPE html>
<html>
<head>
    <title>My Web Page</title>
    <style>
        /* Embedded CSS */
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f0f0f0;
        }
        h1 {
            color: navy;
        }
        p {
            color: green;
        }
        #itemsList {
            margin-top: 20px;
        }
        .item {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>

    <h1>Hello, World!</h1>
    <p>This is my simple web page.</p>

    <!-- Form to Add New Item -->
    <input type="text" id="itemName" placeholder="Enter item name">
    <button id="addItemButton">Add Item</button>

    <!-- Button to Get Items -->
    <button id="getItemsButton">Get Items</button>

    <!-- Display API Response -->
    <p id="apiResponse"></p>

    <!-- List to display items -->
    <ul id="itemsList"></ul>

    <script>
        // Embedded JavaScript
        document.getElementById('addItemButton').addEventListener('click', function() {
            var itemName = document.getElementById('itemName').value;
            fetch('http://localhost:8000/add_item/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({name: itemName})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('apiResponse').textContent = 'Item added with ID: ' + data.id;
                document.getElementById('itemName').value = ''; // Clear input field
                getItems(); // Refresh the items list
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('apiResponse').textContent = 'Failed to add item';
            });
        });

        function deleteItem(itemId) {
            fetch('http://localhost:8000/delete_item/' + itemId, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('apiResponse').textContent = 'Item deleted';
                getItems(); // Refresh the items list
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('apiResponse').textContent = 'Failed to delete item';
            });
        }

        function getItems() {
            fetch('http://localhost:8000/get_items/')
                .then(response => response.json())
                .then(data => {
                    var itemsList = document.getElementById('itemsList');
                    itemsList.innerHTML = ''; // Clear current list
                    data.items.forEach(function(item) {
                        var li = document.createElement('li');
                        li.classList.add('item');
                        li.textContent = item.name + ' ';

                        // Add a delete button for each item
                        var deleteButton = document.createElement('button');
                        deleteButton.textContent = 'Delete';
                        deleteButton.onclick = function() { deleteItem(item.id); };
                        li.appendChild(deleteButton);

                        itemsList.appendChild(li);
                    });
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('apiResponse').textContent = 'Failed to get items';
                });
        }

        document.getElementById('getItemsButton').addEventListener('click', getItems);
    </script>

</body>
</html>
"""



# test_container = test_container.trigger_execution_pipeline(backend_string, dependencies=["FastAPI", "uvicorn"], port="8001")


backend_container = sandbox_backend.trigger_execution_pipeline(backend_string, dependencies=["FastAPI", "uvicorn", "asyncpg", "pydantic"])
print(backend_container.logs(tail=10).decode('utf-8'))


frontend_container = sandbox_frontend.trigger_execution_pipeline(frontend_string)
print(frontend_container.logs(tail=10).decode('utf-8'))

print(sandbox_database.url)
print(sandbox_frontend.url)
print(sandbox_backend.url)
