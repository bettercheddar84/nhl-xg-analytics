#!/usr/bin/env python3
"""
Analyze NHL_AI_TRAINING_FINAL.csv and consolidate with pattern data
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAnalyzer:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.data_path = base_path / "data" / "nhl"
        
    def analyze_training_data(self) -> Dict:
        """Analyze NHL_AI_TRAINING_FINAL.csv structure"""
        logger.info("Loading NHL_AI_TRAINING_FINAL.csv...")
        df = pd.read_csv(self.data_path / "processed" / "NHL_AI_TRAINING_FINAL.csv")
        
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'goal_rate': df['is_goal'].mean() if 'is_goal' in df.columns else None,
            'unique_games': df['game_id'].nunique() if 'game_id' in df.columns else None,
            'unique_shooters': df['shooter_id'].nunique() if 'shooter_id' in df.columns else None,
            'unique_goalies': df['goalie_id'].nunique() if 'goalie_id' in df.columns else None,
            'empty_net_shots': df['empty_net'].sum() if 'empty_net' in df.columns else None,
        }
        
        # Analyze feature distributions
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        analysis['feature_stats'] = {}
        for col in numeric_cols:
            analysis['feature_stats'][col] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'percentiles': df[col].quantile([0.25, 0.5, 0.75]).to_dict()
            }
        
        return analysis
    
    def identify_missing_features(self, current_features: List[str]) -> List[str]:
        """Identify critical features that are missing"""
        critical_features = {
            # Sequence Context
            'rebound_window': 'seconds since last shot',
            'pressure_score': 'from pressure analysis',
            'fatigue_state': 'goalie workload',
            'momentum_score': 'recent goal differential change',
            
            # Player Quality
            'shooter_skill_rating': 'player quality metric',
            'goalie_save_percentage': 'recent performance',
            'shooter_shot_accuracy': 'hit net percentage',
            
            # Spatial Patterns
            'royal_road_pass': 'cross-slot pass indicator',
            'rush_distance': 'distance covered in rush',
            'net_front_presence': 'players in front of net',
            
            # Game Context
            'game_importance': 'playoff race implications',
            'recent_penalties': 'team discipline state',
            'coaching_strategy': 'pull goalie likelihood'
        }
        
        missing = []
        for feature, description in critical_features.items():
            if feature not in current_features:
                missing.append(f"{feature} ({description})")
        
        return missing
    
    def load_pattern_data(self) -> Dict[str, pd.DataFrame]:
        """Load all pattern data files"""
        pattern_files = {
            'fast_break': 'fast_break_patterns.csv',
            'goal_sequences': 'goal_sequences_fixed.csv',
            'goalie_shifts': 'goalie_shift_patterns.csv',
            'goalie_workload': 'goalie_workload.csv',
            'offensive_zone': 'offensive_zone_times.csv',
            'passing': 'passing_sequences.csv',
            'pass_types': 'pass_type_summary.csv',
            'player_shots': 'player_shot_patterns.csv',
            'turnover_risk': 'player_turnover_risk.csv',
            'skater_shifts': 'skater_shift_patterns.csv',
            'pressure': 'turnover_pressure_analysis_60s.csv'
        }
        
        pattern_data = {}
        for name, filename in pattern_files.items():
            filepath = self.data_path / "processed" / filename
            if filepath.exists():
                logger.info(f"Loading {filename}...")
                pattern_data[name] = pd.read_csv(filepath)
            else:
                logger.warning(f"Pattern file not found: {filename}")
        
        return pattern_data
    
    def analyze_pattern_data(self, pattern_data: Dict[str, pd.DataFrame]) -> Dict:
        """Analyze structure of pattern data"""
        pattern_analysis = {}
        
        for name, df in pattern_data.items():
            pattern_analysis[name] = {
                'shape': df.shape,
                'columns': list(df.columns),
                'sample_data': df.head(2).to_dict() if len(df) > 0 else {}
            }
        
        return pattern_analysis
    
    def create_consolidation_plan(self, training_analysis: Dict, pattern_analysis: Dict) -> Dict:
        """Create a plan for consolidating data"""
        plan = {
            'merge_operations': [],
            'feature_engineering': [],
            'validation_checks': []
        }
        
        # Identify merge keys
        training_cols = training_analysis['columns']
        
        # Plan merges based on available keys
        if 'game_id' in training_cols:
            plan['merge_operations'].append({
                'type': 'game_level',
                'datasets': ['pressure', 'offensive_zone', 'goal_sequences'],
                'key': 'game_id'
            })
        
        if 'shooter_id' in training_cols:
            plan['merge_operations'].append({
                'type': 'player_level',
                'datasets': ['player_shots', 'turnover_risk'],
                'key': 'shooter_id'
            })
        
        if 'goalie_id' in training_cols:
            plan['merge_operations'].append({
                'type': 'goalie_level',
                'datasets': ['goalie_workload', 'goalie_shifts'],
                'key': 'goalie_id'
            })
        
        # Feature engineering plan
        plan['feature_engineering'] = [
            'Calculate rebound windows from shot sequences',
            'Aggregate pressure scores by game period',
            'Compute fatigue metrics from goalie workload',
            'Create momentum features from score differential changes',
            'Extract rush patterns from fast break data'
        ]
        
        # Validation checks
        plan['validation_checks'] = [
            'Ensure no data leakage (future information)',
            'Validate merge completeness (% matched records)',
            'Check for duplicate features after merge',
            'Verify goal rate consistency',
            'Validate time-based features are logical'
        ]
        
        return plan
    
    def generate_report(self, analysis_results: Dict) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("# NHL Data Analysis Report\n")
        
        # Training data summary
        training = analysis_results['training_data']
        report.append("## Training Data Summary")
        report.append(f"- Shape: {training['shape']}")
        report.append(f"- Goal Rate: {training['goal_rate']:.3%}")
        report.append(f"- Unique Games: {training['unique_games']:,}")
        report.append(f"- Unique Shooters: {training['unique_shooters']:,}")
        report.append(f"- Unique Goalies: {training['unique_goalies']:,}")
        report.append(f"- Empty Net Shots: {training['empty_net_shots']:,}\n")
        
        # Missing features
        report.append("## Missing Critical Features")
        for feature in analysis_results['missing_features']:
            report.append(f"- {feature}")
        report.append("")
        
        # Pattern data summary
        report.append("## Available Pattern Data")
        for name, info in analysis_results['pattern_analysis'].items():
            report.append(f"\n### {name}")
            report.append(f"- Shape: {info['shape']}")
            report.append(f"- Columns: {', '.join(info['columns'][:5])}...")
        
        # Consolidation plan
        report.append("\n## Data Consolidation Plan")
        plan = analysis_results['consolidation_plan']
        
        report.append("\n### Merge Operations")
        for merge in plan['merge_operations']:
            report.append(f"- {merge['type']}: {', '.join(merge['datasets'])} on {merge['key']}")
        
        report.append("\n### Feature Engineering Steps")
        for step in plan['feature_engineering']:
            report.append(f"- {step}")
        
        report.append("\n### Validation Checks")
        for check in plan['validation_checks']:
            report.append(f"- {check}")
        
        return '\n'.join(report)

def main():
    """Main analysis function"""
    base_path = Path("/mnt/c/Users/Robert Wolfe/Desktop/renewed-solutions/penguins_ai")
    analyzer = DataAnalyzer(base_path)
    
    results = {}
    
    # Analyze training data
    logger.info("Analyzing training data...")
    results['training_data'] = analyzer.analyze_training_data()
    
    # Identify missing features
    current_features = results['training_data']['columns']
    results['missing_features'] = analyzer.identify_missing_features(current_features)
    
    # Load and analyze pattern data
    logger.info("Loading pattern data...")
    pattern_data = analyzer.load_pattern_data()
    results['pattern_analysis'] = analyzer.analyze_pattern_data(pattern_data)
    
    # Create consolidation plan
    logger.info("Creating consolidation plan...")
    results['consolidation_plan'] = analyzer.create_consolidation_plan(
        results['training_data'], 
        results['pattern_analysis']
    )
    
    # Generate report
    report = analyzer.generate_report(results)
    
    # Save results
    output_dir = base_path / "data" / "nhl" / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON results
    with open(output_dir / "data_analysis_results.json", 'w') as f:
        # Convert numpy types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            return obj
        
        json.dump(results, f, indent=2, default=convert_types)
    
    # Save report
    with open(output_dir / "data_analysis_report.md", 'w') as f:
        f.write(report)
    
    print(report)
    logger.info(f"Analysis complete! Results saved to {output_dir}")

if __name__ == "__main__":
    main()