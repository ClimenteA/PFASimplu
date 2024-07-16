const socket = new WebSocket("ws://localhost:15173");

socket.addEventListener("open", (event) => {
    console.log("WebSocket connection opened");
});

socket.addEventListener("message", (event) => {
    console.log("Message from server:", event.data);
    if (event.data === 'reload') {
        location.reload();
    }
});

socket.addEventListener("close", (event) => {
    console.log("WebSocket connection closed");
});

socket.addEventListener("error", (event) => {
    console.error("WebSocket error:", event);
});
