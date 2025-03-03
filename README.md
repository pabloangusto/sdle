# ShoppingList App following Amazon Dynamo Architecture and CRDTs
## Instructions to run the project

To run the project, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/pabloangusto/sdle.git
    cd src
    ```

2. **Run the broker**:
    ```bash
    python3 broker/broker.py
    ```

3. **Run a server**:
    The `id` argument indicates the server ID. Start by executing server 0. Then you can add other servers with different IDs.
    ```bash
    python3 server/server.py 0
    ```
    ```bash
    python3 server/server.py <id>
    ```

4. **Run a client**:
    ```bash
    python3 client/client.py
    ```
