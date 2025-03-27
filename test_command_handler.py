from features.command_handler import CommandHandler

handler = CommandHandler()
test_commands = [
    "open chrome",
    "launch spotify",
    "open notepad",
    "search google for python tutorials",
    "remember this command: 'open notes' → 'notepad.exe'"
]

for cmd in test_commands:
    result = handler.execute_command(cmd)
    print(f"Command: {cmd}")
    print(f"Result: {result}\n") 