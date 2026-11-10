# RPG Character Tracker - Sprint 1
# This program lets the user create characters and manage their hit points.
# HP calculations are handled by a separate ZeroMQ microservice.

import zmq


# Ask for a positive whole number. B returns to the menu.
def get_number(message):
    while True:
        answer = input(message).strip()
        if answer.upper() == 'B':
            return None
        if answer.isdigit() and int(answer) > 0:
            return int(answer)
        print('Please enter a positive whole number or B to cancel.')


# Add a character to the list. New characters start with full HP.
def create_character(characters):
    print('\nCREATE CHARACTER')
    name = input('Name (B to cancel): ').strip()
    if name.upper() == 'B':
        return
    if name == '':
        print('Name cannot be blank.')
        return

    character_class = input('Class (B to cancel): ').strip()
    if character_class.upper() == 'B':
        return
    if character_class == '':
        print('Class cannot be blank.')
        return

    maximum = get_number('Maximum HP (B to cancel): ')
    if maximum is None:
        return

    character = {'name': name, 'class': character_class,
                 'hp': maximum, 'max_hp': maximum}
    characters.append(character)
    print(f'Created {name} with {maximum} HP.')


# Show all characters and return the one selected by the user.
def choose_character(characters):
    if len(characters) == 0:
        print('No characters yet. Create one first.')
        return None

    print('\nCHARACTERS')
    for i in range(len(characters)):
        character = characters[i]
        print(f"{i + 1}. {character['name']} - {character['class']} "
              f"({character['hp']}/{character['max_hp']} HP)")

    while True:
        choice = input('Choose a number (B to cancel): ').strip()
        if choice.upper() == 'B':
            return None
        if choice.isdigit():
            number = int(choice)
            if 1 <= number <= len(characters):
                return characters[number - 1]
        print('Please choose a listed number.')


# Display the selected character's information.
def view_character(characters):
    character = choose_character(characters)
    if character is None:
        return
    print(f"\nName: {character['name']}")
    print(f"Class: {character['class']}")
    print(f"Current HP: {character['hp']}")
    print(f"Maximum HP: {character['max_hp']}")


# Send an HP request to the microservice and receive its calculation.
def ask_hp_service(socket, character, action, amount):
    request = {'current_hp': character['hp'],
               'max_hp': character['max_hp'],
               'amount': amount, 'action': action}
    try:
        socket.send_json(request)       # REQ: send a JSON message
        response = socket.recv_json()   # Wait for the REP service's reply
    except zmq.ZMQError:
        print('Could not contact the HP service. No HP was changed.')
        return None

    if response.get('status') == 'success':
        return response['new_hp']
    print('HP service error:', response.get('message', 'Unknown error'))
    return None


# Preview damage/healing before applying it; allow undo afterward.
def update_hp(characters, socket):
    character = choose_character(characters)
    if character is None:
        return

    while True:
        choice = input('D = Damage, H = Healing, B = Cancel: ').strip().upper()
        if choice == 'B':
            return
        if choice == 'D':
            action = 'damage'
            break
        if choice == 'H':
            action = 'heal'
            break
        print('Please enter D or H.')

    amount = get_number('Amount (B to cancel): ')
    if amount is None:
        return

    while True:
        new_hp = ask_hp_service(socket, character, action, amount)
        if new_hp is None:
            return

        print(f"\nPreview: {character['name']} "
              f"{character['hp']} -> {new_hp} HP ({amount} {action})")
        print('Y = Apply, T = Try another amount, S = Switch action, N = Cancel')
        choice = input('Choice: ').strip().upper()

        if choice == 'Y':
            old_hp = character['hp']  # Save old value in case user wants undo
            character['hp'] = new_hp
            print(f"HP updated: {character['hp']}/{character['max_hp']}")
            undo = input('U = Undo, Enter = Keep change: ').strip().upper()
            if undo == 'U':
                character['hp'] = old_hp
                print(f'Change undone. HP restored to {old_hp}.')
            return
        elif choice == 'T':
            amount = get_number('New amount (B to cancel): ')
            if amount is None:
                return
        elif choice == 'S':
            if action == 'damage':
                action = 'heal'
            else:
                action = 'damage'
        elif choice in ('N', 'B'):
            print('No change was made.')
            return
        else:
            print('Please enter Y, T, S, or N.')


# Main menu and ZeroMQ client setup.
def main():
    characters = []  # Stored only while this program is running

    context = zmq.Context()
    socket = context.socket(zmq.REQ)  # REQ means request (client)
    socket.connect('tcp://127.0.0.1:5555')

    try:
        while True:
            print('\nRPG CHARACTER TRACKER')
            print('1. Create Character')
            print('2. View Character')
            print('3. Update Hit Points')
            print('4. Exit')
            choice = input('Choose 1-4: ').strip()

            if choice == '1':
                create_character(characters)
            elif choice == '2':
                view_character(characters)
            elif choice == '3':
                update_hp(characters, socket)
            elif choice == '4':
                print('Goodbye! Characters are not saved after exit.')
                break
            else:
                print('Please choose 1, 2, 3, or 4.')
    except (KeyboardInterrupt, EOFError):
        print('\nProgram stopped.')
    finally:
        socket.close(0)
        context.term()


if __name__ == '__main__':
    main()
