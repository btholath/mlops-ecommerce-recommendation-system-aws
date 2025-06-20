# src/data_preparation/data_validation.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import boto3
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Comprehensive data validation and quality assessment
    """
    
    def __init__(self):
        self.validation_results = {}
        self.quality_metrics = {}
        
    def validate_data_schema(self, df: pd.DataFrame, 
                           expected_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate data schema against expected structure
        """
        validation_result = {
            'schema_valid': True,
            'missing_columns': [],
            'unexpected_columns': [],
            'type_mismatches': {}
        }
        
        # Check for missing expected columns
        expected_cols = set(expected_schema.keys())
        actual_cols = set(df.columns)
        
        missing_cols = expected_cols - actual_cols
        unexpected_cols = actual_cols - expected_cols
        
        validation_result['missing_columns'] = list(missing_cols)
        validation_result['unexpected_columns'] = list(unexpected_cols)
        
        if missing_cols or unexpected_cols:
            validation_result['schema_valid'] = False
        
        # Check data types
        for col, expected_type in expected_schema.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if not self._types_compatible(actual_type, expected_type):
                    validation_result['type_mismatches'][col] = {
                        'expected': expected_type,
                        'actual': actual_type
                    }
                    validation_result['schema_valid'] = False
        
        logger.info(f"Schema validation completed. Valid: {validation_result['schema_valid']}")
        return validation_result
    
    def _types_compatible(self, actual_type: str, expected_type: str) -> bool:
        """Check if data types are compatible"""
        type_mappings = {
            'int64': ['int', 'integer', 'numeric'],
            'float64': ['float', 'numeric', 'decimal'],
            'object': ['string', 'text', 'categorical'],
            'datetime64[ns]': ['datetime', 'timestamp'],
            'bool': ['boolean', 'bool']
        }
        
        for actual, compatible_list in type_mappings.items():
            if actual in actual_type.lower():
                return expected_type.lower() in compatible_list
        
        return False
    
    def check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive data quality assessment
        """
        quality_report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_value_summary': {},
            'duplicate_rows': 0,
            'outlier_summary': {},
            'data_distribution': {},
            'quality_score': 0.0
        }
        
        # Missing value analysis
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_percentage = (missing_count / len(df)) * 100
            quality_report['missing_value_summary'][col] = {
                'count': int(missing_count),
                'percentage': round(missing_percentage, 2)
            }
        
        # Duplicate rows
        quality_report['duplicate_rows'] = df.duplicated().sum()
        
        # Outlier detection for numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            quality_report['outlier_summary'][col] = {
                'count': len(outliers),
                'percentage': round((len(outliers) / len(df)) * 100, 2)
            }
        
        # Data distribution summary
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                quality_report['data_distribution'][col] = {
                    'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                    'median': float(df[col].median()) if not df[col].isnull().all() else None,
                    'std': float(df[col].std()) if not df[col].isnull().all() else None,
                    'min': float(df[col].min()) if not df[col].isnull().all() else None,
                    'max': float(df[col].max()) if not df[col].isnull().all() else None
                }
            else:
                unique_values = df[col].nunique()
                quality_report['data_distribution'][col] = {
                    'unique_values': int(unique_values),
                    'most_common': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None
                }
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(quality_report)
        quality_report['quality_score'] = quality_score
        
        logger.info(f"Data quality assessment completed. Score: {quality_score}")
        return quality_report
    
    def _calculate_quality_score(self, quality_report: Dict) -> float:
        """Calculate overall data quality score (0-100)"""
        score = 100.0
        
        # Deduct points for missing values
        total_missing_percentage = sum([
            metrics['percentage'] 
            for metrics in quality_report['missing_value_summary'].values()
        ]) / len(quality_report['missing_value_summary'])
        score -= min(total_missing_percentage * 0.5, 30)
        
        # Deduct points for duplicates
        if quality_report['total_rows'] > 0:
            duplicate_percentage = (quality_report['duplicate_rows'] / quality_report['total_rows']) * 100
            score -= min(duplicate_percentage * 0.3, 20)
        
        # Deduct points for excessive outliers
        total_outlier_percentage = sum([
            metrics['percentage'] 
            for metrics in quality_report['outlier_summary'].values()
        ]) / max(len(quality_report['outlier_summary']), 1)
        score -= min(total_outlier_percentage * 0.2, 15)
        
        return max(score, 0.0)
    
    def validate_business_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate business-specific rules for e-commerce data
        """
        business_validation = {
            'valid': True,
            'violations': []
        }
        
        # Rule 1: Transaction amounts should be positive
        if 'transaction_amount' in df.columns:
            negative_amounts = df[df['transaction_amount'] <= 0]
            if len(negative_amounts) > 0:
                business_validation['violations'].append({
                    'rule': 'positive_transaction_amounts',
                    'violation_count': len(negative_amounts),
                    'description': 'Transaction amounts must be positive'
                })
                business_validation['valid'] = False
        
        # Rule 2: Customer age should be reasonable (18-120)
        if 'age' in df.columns:
            invalid_ages = df[(df['age'] < 18) | (df['age'] > 120)]
            if len(invalid_ages) > 0:
                business_validation['violations'].append({
                    'rule': 'reasonable_customer_age',
                    'violation_count': len(invalid_ages),
                    'description': 'Customer age should be between 18 and 120'
                })
                business_validation['valid'] = False
        
        # Rule 3: Dates should not be in the future
        date_columns = ['transaction_timestamp', 'registration_date']
        current_time = datetime.now()
        
        for col in date_columns:
            if col in df.columns:
                future_dates = df[pd.to_datetime(df[col]) > current_time]
                if len(future_dates) > 0:
                    business_validation['violations'].append({
                        'rule': f'no_future_dates_{col}',
                        'violation_count': len(future_dates),
                        'description': f'{col} should not be in the future'
                    })
                    business_validation['valid'] = False
        
        logger.info(f"Business rule validation completed. Valid: {business_validation['valid']}")
        return business_validation
    
    def detect_data_drift(self, reference_df: pd.DataFrame, 
                         current_df: pd.DataFrame,
                         numerical_threshold: float = 0.1,
                         categorical_threshold: float = 0.1) -> Dict[str, Any]:
        """
        Detect data drift between reference and current datasets
        """
        drift_report = {
            'drift_detected': False,
            'numerical_drift': {},
            'categorical_drift': {},
            'overall_drift_score': 0.0
        }
        
        common_columns = set(reference_df.columns) & set(current_df.columns)
        
        for col in common_columns:
            if reference_df[col].dtype in ['int64', 'float64']:
                # Statistical test for numerical columns (simplified KS test)
                ref_mean = reference_df[col].mean()
                cur_mean = current_df[col].mean()
                ref_std = reference_df[col].std()
                
                if ref_std != 0:
                    drift_score = abs(cur_mean - ref_mean) / ref_std
                    drift_report['numerical_drift'][col] = {
                        'drift_score': float(drift_score),
                        'drift_detected': drift_score > numerical_threshold,
                        'reference_mean': float(ref_mean),
                        'current_mean': float(cur_mean)
                    }
                    
                    if drift_score > numerical_threshold:
                        drift_report['drift_detected'] = True
            
            else:
                # Chi-square test for categorical columns (simplified)
                ref_dist = reference_df[col].value_counts(normalize=True)
                cur_dist = current_df[col].value_counts(normalize=True)
                
                # Calculate distribution difference
                all_categories = set(ref_dist.index) | set(cur_dist.index)
                drift_score = 0
                
                for category in all_categories:
                    ref_prop = ref_dist.get(category, 0)
                    cur_prop = cur_dist.get(category, 0)
                    drift_score += abs(ref_prop - cur_prop)
                
                drift_report['categorical_drift'][col] = {
                    'drift_score': float(drift_score),
                    'drift_detected': drift_score > categorical_threshold
                }
                
                if drift_score > categorical_threshold:
                    drift_report['drift_detected'] = True
        
        # Calculate overall drift score
        all_scores = []
        all_scores.extend([d['drift_score'] for d in drift_report['numerical_drift'].values()])
        all_scores.extend([d['drift_score'] for d in drift_report['categorical_drift'].values()])
        
        if all_scores:
            drift_report['overall_drift_score'] = float(np.mean(all_scores))
        
        logger.info(f"Data drift detection completed. Drift detected: {drift_report['drift_detected']}")
        return drift_report