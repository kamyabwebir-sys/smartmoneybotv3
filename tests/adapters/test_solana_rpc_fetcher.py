import json

from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.production_shadow import SolanaRPCConfig


class Response:
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self): return json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"slot": 7}}).encode()


def test_rpc_fetcher_normalizes_json_request():
    seen = []
    def opener(request, timeout):
        seen.append((request.get_method(), timeout, json.loads(request.data)))
        return Response()
    result = SolanaRPCFetcher(SolanaRPCConfig("https://rpc.example"), opener).request("getSlot")
    assert result["result"]["slot"] == 7
    assert seen[0][0] == "POST"
