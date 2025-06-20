# tests/test_data_preparation.py
import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_preparation.data_validation import DataValidator
from data_preparation.data_transformation import DataTransformer

class TestDataPreparation(unittest.TestCase):
    
    def setUp(self):
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'customer_id': ['C001', 'C002', 'C003'],
            'age': [25, 35, 45],
            'income': [50000, 60000, 70000],
            'gender': ['Male', 'Female', 'Male']
        })
    
    def test_data_validation(self):
        """Test data validation functionality"""
        schema = {
            'customer_id': 'string',
            'age': 'int',
            'income': 'float',
            'gender': 'string'
        }
        
        result = self.validator.validate_data_schema(self.sample_data, schema)
        self.assertTrue(result['schema_valid'])
    
    def test_data_quality_check(self):
        """Test data quality assessment"""
        quality_report = self.validator.check_data_quality(self.sample_data)
        self.assertGreater(quality_report['quality_score'], 0)
        self.assertEqual(quality_report['total_rows'], 3)

if __name__ == '__main__':
    unittest.main()