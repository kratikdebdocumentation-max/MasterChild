"""
Position and MTM management
"""
from typing import Dict, Any, Optional
from logger import applicationLogger

class PositionManager:
    """Manages positions and MTM calculations"""
    
    def __init__(self):
        pass
    
    def get_positions(self, api) -> list:
        """
        Get positions for an account
        
        Args:
            api: API instance
            
        Returns:
            List of positions
        """
        try:
            return api.get_positions()
        except Exception as e:
            applicationLogger.error(f"Error fetching positions: {e}")
            return []
    
    def calculate_mtm(self, api) -> float:
        """
        Calculate MTM for an account
        
        Args:
            api: API instance
            
        Returns:
            MTM value
        """
        try:
            positions = self.get_positions(api)
            if not positions:
                return 0.0
            
            mtm = 0.0
            pnl = 0.0
            
            for position in positions:
                mtm += float(position.get('urmtom', 0))
                pnl += float(position.get('rpnl', 0))
            
            day_m2m = mtm + pnl
            return day_m2m
            
        except Exception as e:
            applicationLogger.error(f"Error calculating MTM: {e}")
            return 0.0
    
    def get_position_summary(self, api) -> Dict[str, Any]:
        """
        Get position summary for an account
        
        Args:
            api: API instance
            
        Returns:
            Position summary dictionary
        """
        try:
            positions = self.get_positions(api)
            if not positions:
                return {
                    'total_mtm': 0.0,
                    'total_pnl': 0.0,
                    'day_m2m': 0.0,
                    'position_count': 0
                }
            
            total_mtm = 0.0
            total_pnl = 0.0
            position_count = len(positions)
            
            for position in positions:
                total_mtm += float(position.get('urmtom', 0))
                total_pnl += float(position.get('rpnl', 0))
            
            day_m2m = total_mtm + total_pnl
            
            return {
                'total_mtm': total_mtm,
                'total_pnl': total_pnl,
                'day_m2m': day_m2m,
                'position_count': position_count
            }
            
        except Exception as e:
            applicationLogger.error(f"Error getting position summary: {e}")
            return {
                'total_mtm': 0.0,
                'total_pnl': 0.0,
                'day_m2m': 0.0,
                'position_count': 0
            }
