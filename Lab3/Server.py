import os
import sys
import asyncio
import httpx
from quart import Quart, Response, send_from_directory
from http import HTTPStatus

from Lab3.Board import Board
from Lab3.Commands import flip, look, map_card_value, watch, apply_map_command


class WebServer:
    def __init__(self, board: Board, port: int):
        self.board = board
        self.port = port

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PUBLIC_DIR = os.path.join(BASE_DIR, "public")
        self.app = Quart(__name__, static_folder="public", static_url_path="")

        @self.app.after_request
        async def add_cors_headers(response):  # <-- Make this async
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        @self.app.get("/look/<player_id>")
        async def look_route(player_id):
            board_state = await look(self.board, player_id)
            return Response(board_state, status=HTTPStatus.OK, mimetype="text/plain")

        @self.app.get("/flip/<player_id>/<location>")
        async def flip_route(player_id, location):
            try:
                row, column = map(int, location.split(","))
                play_message = await flip(player_id, row, column, self.board)
                board_state = await look(self.board, player_id)
                print(f"[{player_id}] Move result: {play_message}")
                return Response(board_state, status=HTTPStatus.OK, mimetype="text/plain")
            except Exception as e:
                return Response(
                    f"Move failed: {e}",
                    status=HTTPStatus.CONFLICT,
                    mimetype="text/plain",
                )

        @self.app.get("/map/<value>")
        async def map_route(value):
            """This route ACTS AS the async transformer function 'f'."""
            try:
                mapped_value = await map_card_value(value)
                return Response(mapped_value, status=HTTPStatus.OK, mimetype="text/plain")
            except Exception as e:
                return Response(
                    f"error mapping value: {e}",
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    mimetype="text/plain",
                )

        @self.app.get("/apply_map")
        async def apply_map_route():
            """
            This endpoint triggers the map operation.
            It defines the async transformer function 'f'
            which calls our own /map/<value> endpoint.
            """
            try:
                async with httpx.AsyncClient() as client:

                    async def transformer_func(value_to_map: str) -> str:
                        url = f"http://127.0.0.1:{self.port}/map/{value_to_map}"
                        res = await client.get(url)
                        res.raise_for_status()
                        return res.text

                    await apply_map_command(self.board, transformer_func)

                return Response("Map applied successfully", status=HTTPStatus.OK)

            except Exception as e:
                print(f"Error during /apply_map: {e}")
                return Response(f"Failed to apply map: {e}", status=HTTPStatus.INTERNAL_SERVER_ERROR)

        @self.app.get("/watch/<player_id>")
        async def watch_route(player_id):
            board_state = await watch(self.board, player_id)
            return Response(board_state, status=HTTPStatus.OK, mimetype="text/plain")

        @self.app.route("/")
        async def serve_index():
            return await send_from_directory(PUBLIC_DIR, "index.html")


def main():
    if len(sys.argv) < 3:
        print("Usage: python server.py PORT FILENAME")
        sys.exit(1)

    port = int(sys.argv[1])
    filename = sys.argv[2]

    async def run_server():
        board = await Board.parse_from_file(filename)

        server = WebServer(board, port)

        from hypercorn.config import Config
        from hypercorn.asyncio import serve

        config = Config()
        config.bind = [f"0.0.0.0:{port}"]
        config.use_reloader = False

        print(f"✅ Hypercorn server (with Quart) listening at http://localhost:{port}")

        await serve(server.app, config)

    asyncio.run(run_server())


if __name__ == "__main__":
    main()