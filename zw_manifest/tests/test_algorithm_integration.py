import os
import sys
import unittest
import time
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from collections import defaultdict
import odoo
from odoo.tools import config
from odoo.modules.registry import Registry

# Set up Python path for Odoo and custom modules
odoo_path = r'C:\Users\Victor\Desktop\odoo\odoo-16.0'
sys.path.append(os.path.join(odoo_path))
sys.path.append(os.path.join(odoo_path, 'odoo'))
sys.path.append(os.path.join(odoo_path, 'zw_manifest'))
sys.path.append(os.path.join(odoo_path, 'zw_customer'))
sys.path.append(os.path.join(odoo_path, 'zw_mine'))
sys.path.append(os.path.join(odoo_path, 'zw_asset'))
sys.path.append(os.path.join(odoo_path, 'zw_user'))

# Configure Odoo
config['addons_path'] = ','.join([
    os.path.join(odoo_path, 'odoo', 'addons'),
    odoo_path  # Include root directory for custom modules
])
config['db_name'] = 'odoo'  # Replace with your actual database name
config['db_password'] = 'odoo'
config['db_user'] = 'victor'

# Initialize Odoo registry
Registry.new(config['db_name'], update_module=True)

# Import custom module classes and functions
from zw_manifest.models.manifest import ManifestStack, ManifestPriorityQueue, validate_dt_number, find_shortest_path
from zw_customer.models.customer_management import CustomerHashTable
from zw_mine.models.mine_management import MineBST
from zw_asset.models.asset_management import AssetHeap
from zw_manifest.models.route import CollectionGraph
from zw_user.models.audit_log import kmp_search

class TestAlgorithmIntegration(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create test data
        self.customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat_number': 'ZA123456789'
        })
        self.mine = self.env['mine.mine'].create({
            'name': 'Test Mine',
            'mine_code': 'M001',
            'sawis_number': 'SAWIS123',
            'latitude': -26.0,
            'longitude': 28.0
        })
        self.disposal_site = self.env['disposal.site'].create({
            'name': 'Test Disposal Site',
            'sawis_number': 'SAWIS456',
            'latitude': -26.1,
            'longitude': 28.1
        })
        self.waste_type = self.env['waste.type'].create({
            'name': 'General Waste'
        })
        self.hazardous_waste_type = self.env['waste.type'].create({
            'name': 'Hazardous Waste'
        })
        self.manifest = self.env['waste.manifest'].create({
            'manifest_id': 'MF001',
            'customer_id': self.customer.id,
            'mine_id': self.mine.id,
            'disposal_site_id': self.disposal_site.id,
            'sawis_number': 'SAWIS123',
            'status': 'booked',
            'waste_type_id': self.waste_type.id
        })
        self.schedule = self.env['waste.schedule'].create({
            'customer_id': self.customer.id,
            'mine_id': self.mine.id,
            'waste_type_id': self.waste_type.id,
            'scheduled_date': '2025-08-05',
            'manifest_id': self.manifest.id
        })
        self.driver = self.env['res.users'].create({
            'name': 'Test Driver',
            'login': 'driver@test.com',
            'custom_role': 'driver'
        })
        self.asset = self.env['stock.quant'].create({
            'product_id': self.env['product.product'].create({'name': 'Test Bin', 'is_asset': True}).id,
            'location_id': self.env['stock.location'].create({'name': 'Test Location'}).id,
            'quantity': 1,
            'condition': 'intact'
        })

    # Data Structure Tests
    def test_manifest_stack(self):
        stack = ManifestStack()
        stack.push('MF001', 'booked')
        stack.push('MF001', 'generated')
        self.assertEqual(stack.pop()['status'], 'generated')
        self.assertEqual(stack.pop()['status'], 'booked')

    def test_manifest_priority_queue(self):
        pq = ManifestPriorityQueue()
        pq.push('MF001', 1)
        pq.push('MF002', 0)
        self.assertEqual(pq.pop(), 'MF002')

    def test_validate_dt_number(self):
        self.assertTrue(validate_dt_number('DT123456'))
        self.assertFalse(validate_dt_number('DT123'))

    def test_customer_hash_table(self):
        ht = CustomerHashTable()
        ht.insert({'id': self.customer.id, 'vat_number': 'ZA123456789'})
        result = ht.get('ZA123456789')
        self.assertEqual(result['id'], self.customer.id)

    def test_mine_bst(self):
        bst = MineBST()
        bst.insert('M001', 'SAWIS123')
        result = bst.search('SAWIS123')
        self.assertEqual(result, 'M001')

    def test_asset_heap(self):
        heap = AssetHeap()
        heap.push(self.asset.id, 0)
        self.assertEqual(heap.pop(), self.asset.id)

    def test_collection_graph(self):
        graph = CollectionGraph()
        graph.add_edge('M001', 'SAWIS456', 0.1414)
        self.assertEqual(graph.graph['M001'], [('SAWIS456', 0.1414)])

    # Algorithm Tests
    def test_dijkstra_correct_path(self):
        graph = defaultdict(list)
        graph['M001'] = [('SAWIS456', 0.1414)]
        graph['SAWIS456'] = [('M001', 0.1414)]
        distance, path = find_shortest_path(graph, 'M001', 'SAWIS456')
        self.assertAlmostEqual(distance, 0.1414, places=4)
        self.assertEqual(path, ['M001', 'SAWIS456'])

    def test_dijkstra_unreachable_node(self):
        graph = defaultdict(list)
        graph['M001'] = []
        graph['SAWIS456'] = []
        distance, path = find_shortest_path(graph, 'M001', 'SAWIS456')
        self.assertEqual(distance, float('inf'))
        self.assertEqual(path, [])

    def test_dijkstra_negative_weights(self):
        graph = defaultdict(list)
        graph['M001'] = [('SAWIS456', -1.0)]
        with self.assertRaises(ValueError):
            find_shortest_path(graph, 'M001', 'SAWIS456')

    def test_dijkstra_performance(self):
        graph = defaultdict(list)
        for i in range(100):
            node = f'N{i}'
            for j in range(100):
                if i != j:
                    graph[node].append((f'N{j}', 1.0))
        start_time = time.time()
        find_shortest_path(graph, 'N0', 'N99')
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 0.5)  # Relaxed threshold for robustness

    def test_kmp_correct_match(self):
        text = "Manifest created with SAWIS123"
        pattern = "SAWIS123"
        indices = kmp_search(text, pattern, case_sensitive=False)
        self.assertEqual(indices, [20])

    def test_kmp_no_match(self):
        text = "Manifest created with SAWIS123"
        pattern = "SAWIS999"
        indices = kmp_search(text, pattern, case_sensitive=False)
        self.assertEqual(indices, [])

    def test_kmp_case_insensitivity(self):
        text = "Manifest created with sawis123"
        pattern = "SAWIS123"
        indices = kmp_search(text, pattern, case_sensitive=False)
        self.assertEqual(indices, [20])

    def test_kmp_performance(self):
        large_log = "SAWIS123 " * 125000
        self.env['audit.log'].create({
            'model_name': 'waste.manifest',
            'record_id': self.manifest.id,
            'operation': 'create',
            'changes': large_log
        })
        start_time = time.time()
        kmp_search(large_log, 'SAWIS123', case_sensitive=False)
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 0.5)  # Relaxed threshold for robustness

    # Integration Tests
    def test_dijkstra_manifest_integration(self):
        self.manifest.write({'status': 'generated'})
        self.manifest.action_advance_status()  # Advances to scheduled
        self.assertTrue(self.manifest.optimized_route, "Route not optimized")
        self.assertGreater(self.manifest.route_distance, 0, "Route distance not calculated")

    def test_schedule_route_status(self):
        self.manifest.write({'status': 'generated'})
        self.manifest.action_advance_status()
        self.assertEqual(self.schedule.route_status, self.manifest.optimized_route, "Schedule route status mismatch")

    def test_driver_role_restriction(self):
        with self.assertRaises(ValidationError):
            self.manifest.with_user(self.driver).action_advance_status()

    def test_hazardous_waste_compliance(self):
        self.manifest.write({'waste_type_id': self.hazardous_waste_type.id, 'dt_number': 'INVALID'})
        with self.assertRaises(ValidationError):
            self.manifest._check_dt_number()

if __name__ == '__main__':
    unittest.main()