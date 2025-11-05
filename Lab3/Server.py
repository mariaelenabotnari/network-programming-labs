import sys
import asyncio
import time

from flask import Flask, Response, send_from_directory
from http import HTTPStatus

from Lab3.Board import Board
from Lab3.Commands import flip, look, map_card_value, watch, check_matching_cards


class WebServer:
    def __init__(self, board: Board, port: int):
        self.board = board
        self.port = port
        self.app = Flask(__name__, static_folder="public", static_url_path="")

        @self.app.after_request
        def add_cors_headers(response):
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

                check_existence_matching_cards = await flip(player_id, row, column, self.board)

                if check_existence_matching_cards:
                    asyncio.create_task(check_matching_cards(player_id, self.board))

                board_state = await look(self.board, player_id)
                return Response(board_state, status=HTTPStatus.OK, mimetype="text/plain")
            except Exception as e:
                return Response(
                    f"cannot flip this card: {e}",
                    status=HTTPStatus.CONFLICT,
                    mimetype="text/plain",
                )

        @self.app.get("/map/<value>")
        async def map_route(value):
            try:
                mapped_value = await map_card_value(value)
                return Response(mapped_value, status=HTTPStatus.OK, mimetype="text/plain")
            except Exception as e:
                return Response(
                    f"error mapping value: {e}",
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    mimetype="text/plain",
                )

        @self.app.get("/watch/<player_id>")
        async def watch_route(player_id):
            board_state = await watch(self.board, player_id)
            return Response(board_state, status=HTTPStatus.OK, mimetype="text/plain")

        @self.app.route("/")
        def serve_index():
            return send_from_directory("public", "index.html")

    def start(self):
        print(f"✅ Server listening at http://localhost:{self.port}")
        self.app.run(host="0.0.0.0", port=self.port, debug=False)


def main():
    if len(sys.argv) < 3:
        print("Usage: python server.py PORT FILENAME")
        sys.exit(1)

    port = int(sys.argv[1])
    filename = sys.argv[2]

    board = asyncio.run(Board.parse_from_file(filename))

    server = WebServer(board, port)

    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.use_reloader = True

    print(f"✅ Hypercorn server listening at http://localhost:{port}")

    asyncio.run(serve(server.app, config))


if __name__ == "__main__":
    main()  # Just call the regular main function
