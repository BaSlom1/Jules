import sys
import os

try:
    import winreg
except ImportError:
    winreg = None

def add_to_registry(executable_path):
    if winreg is None:
        print("winreg is not available on this platform.")
        return False

    app_name = "ЧЗХ?"

    # We want to add the context menu to files (*) and folders (Directory)
    keys_to_add = [
        (r"Software\Classes\*\shell\CHZH", f"\"{executable_path}\" \"%1\""),
        (r"Software\Classes\Directory\shell\CHZH", f"\"{executable_path}\" \"%1\"")
    ]

    try:
        for key_path, command in keys_to_add:
            # Create or open the shell key
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

            # Set the default value to the app name
            winreg.SetValue(key, "", winreg.REG_SZ, app_name)

            # Set an icon (optional, using the executable's icon)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, executable_path)

            # Create the command subkey
            command_key = winreg.CreateKey(key, "command")
            winreg.SetValue(command_key, "", winreg.REG_SZ, command)

            winreg.CloseKey(command_key)
            winreg.CloseKey(key)

        return True
    except Exception as e:
        print(f"Failed to add to registry: {e}")
        return False

def remove_from_registry():
    if winreg is None:
        print("winreg is not available on this platform.")
        return False

    keys_to_remove = [
        r"Software\Classes\*\shell\CHZH",
        r"Software\Classes\Directory\shell\CHZH"
    ]

    success = True
    for key_path in keys_to_remove:
        try:
            # Need to delete subkeys first before deleting the main key
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error deleting command key for {key_path}: {e}")

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error deleting key {key_path}: {e}")
            success = False

    return success

if __name__ == "__main__":
    # Test
    if add_to_registry(sys.executable):
        print("Added to registry successfully.")
        remove_from_registry()
        print("Removed from registry successfully.")
