#!/usr/bin/env python3

with open('gui/main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the problematic section and replace it completely
# Look for the section around line 1025-1060
start_idx = 1024  # 0-based index for line 1025
end_idx = 1060

# Find the actual start and end of the problematic section
for i in range(start_idx, min(len(lines), end_idx)):
    if 'if api:' in lines[i]:
        start_idx = i
        break

for i in range(start_idx, min(len(lines), end_idx)):
    if 'applicationLogger.info(f"Using cached' in lines[i]:
        end_idx = i + 1
        break

# Replace the problematic section
replacement = [
    '                if api:\n',
    '                    current_price = self.symbol_manager.get_index_price(api, index)\n',
    '                    if current_price:\n',
    '                        # Update cached price\n',
    '                        self.index_price_manager.update_index_price(index, current_price)\n',
    '                        applicationLogger.info(f"Fetched and cached {index} price: {current_price}")\n',
    '                    else:\n',
    '                        # Price fetch failed - show error popup\n',
    '                        applicationLogger.error(f"Could not fetch price for {index}")\n',
    '                        messagebox.showerror("Price Fetch Error", f"Could not fetch current price for {index}. Please ensure:\\n1. Master account is logged in\\n2. Internet connection is stable\\n3. Market is open\\n\\nPlease try again after checking these conditions.")\n',
    '                        self.strike_dropdown[\'values\'] = []\n',
    '                        return\n',
    '                else:\n',
    '                    # No API available - show error popup\n',
    '                    applicationLogger.error("Master account API not available")\n',
    '                    messagebox.showerror("API Error", "Master account API is not available. Please:\\n1. Login to Master account first\\n2. Check your internet connection\\n3. Restart the application if needed")\n',
    '                    self.strike_dropdown[\'values\'] = []\n',
    '                    return\n',
    '                \n',
    '                applicationLogger.info(f"Using cached {index} price: {current_price}")\n'
]

# Replace the section
new_lines = lines[:start_idx] + replacement + lines[end_idx:]

with open('gui/main_window.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print(f'Fixed section from line {start_idx+1} to {end_idx}')
