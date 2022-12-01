import os
import logging
import unittest
from batch_rpc_provider import BatchRpcProvider, BatchRpcException

POLYGON_RPC_ENDPOINT = os.environ.get('POLYGON_RPC_ENDPOINT', 'https://polygon-rpc.com')


class TestSimple(unittest.IsolatedAsyncioTestCase):
    async def test_error(self):
        try:
            # errors are expected so disable them to avoid confusion
            logging.getLogger("batch_rpc_provider.batch_rpc_provider").setLevel(logging.CRITICAL)
            p = BatchRpcProvider('http://dummy:8545', 10000)
            await p.get_chain_id()
        except BatchRpcException as ex:
            self.assertTrue("aiohttp.ClientConnectorError" in str(ex))
        except Exception as ex:
            self.fail("Unexpected exception: {}".format(ex))

    async def test_polygon_chain_id(self):
        p = BatchRpcProvider(POLYGON_RPC_ENDPOINT, 10000)
        chain_id = await p.get_chain_id()
        self.assertEqual(chain_id, 137)

    async def test_polygon_blocknum(self):
        p = BatchRpcProvider(POLYGON_RPC_ENDPOINT, 10000)
        block_num = await p.get_latest_block()
        self.assertTrue(block_num > 30000000)

    async def test_polygon_block_by_number(self):
        p = BatchRpcProvider(POLYGON_RPC_ENDPOINT, 10000)
        block_info = await p.get_block_by_number(20000000, False)
        expected_transaction_hash = "0x47d74bdc8e8b321b4e1df7e4661c1dcf4f10d7defe8582f6cda0ada0d9ab79f9"
        self.assertEqual(block_info['transactions'][10], expected_transaction_hash)

    async def test_polygon_multi_block_by_number(self):
        p = BatchRpcProvider(POLYGON_RPC_ENDPOINT, 10000)
        blocks_info = await p.get_blocks_by_range(19999999, 2, False)
        expected_transaction_hash = "0x47d74bdc8e8b321b4e1df7e4661c1dcf4f10d7defe8582f6cda0ada0d9ab79f9"
        self.assertEqual(blocks_info[1]['transactions'][10], expected_transaction_hash)


if __name__ == '__main__':
    unittest.main()
