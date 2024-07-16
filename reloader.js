import { watch } from "fs";


let server = Bun.serve({
  port: 15173,
  hostname: "127.0.0.1",
  development: false,
  fetch(req, server) {
    if (server.upgrade(req)) {
      return;
    }
    return new Response("Reloader server ready");
  },
  websocket: {
    open(ws) {
      console.log("WebSocket connection opened");
      
      watch(
        import.meta.dir,
        { recursive: true },
        async (event, filename) => {
        if (filename) {
            console.log(`Detected ${event} in ${filename}. Sending reload...`);
            ws.send('reload');
            console.log("Sent!");
          }
        }
      );
    },
    message(ws, message) {
      console.log(`Received message: ${message}`);
    },
    close(ws, code, message) {
      console.log(`WebSocket closed: ${code} ${message}`);
    },
  },
});


console.info(`Reloader server listening on ${server.hostname} on port ${server.port}` )