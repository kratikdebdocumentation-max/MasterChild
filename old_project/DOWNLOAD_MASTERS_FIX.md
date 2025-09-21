# Download Masters Fix

## 🔍 **Issue Identified**
The `downloadMasters_v0.py` file was trying to find NFO symbol files in the current directory, but we moved all symbol files to the `data/` folder. This caused a `ValueError: max() iterable argument is empty` error.

## ✅ **Fix Applied**

### **Problem**
```python
# OLD CODE - Looking in current directory
nfo_file = max(
    (file for file in os.listdir() if file.startswith('NFO_symbols') and file.endswith('.txt')),
    key=lambda f: datetime.strptime(f.split('_')[-1].replace('.txt', ''), '%Y-%m-%d')
)
```

### **Solution**
```python
# NEW CODE - Looking in data directory
nfo_file = max(
    (file for file in os.listdir('data') if file.startswith('NFO_symbols') and file.endswith('.txt')),
    key=lambda f: datetime.strptime(f.split('_')[-1].replace('.txt', ''), '%Y-%m-%d')
)
nfo_file = os.path.join('data', nfo_file)  # Add data folder path
```

## 🎯 **Changes Made**

1. **Updated Directory Search**: Changed `os.listdir()` to `os.listdir('data')`
2. **Added Path Construction**: Used `os.path.join('data', nfo_file)` to create full path
3. **Maintained Functionality**: All other functionality remains the same

## ✅ **Result**
- ✅ **Error Fixed**: No more `ValueError: max() iterable argument is empty`
- ✅ **Data Folder Support**: Correctly finds files in `data/` folder
- ✅ **Backward Compatibility**: Still works with existing functionality
- ✅ **Clean Code**: Proper path handling

## 🚀 **Application Status**
The application should now start successfully without the download masters error. All symbol files are properly organized in the `data/` folder and the code correctly references them.
