# HP Calculation Microservice - Sprint 1
# Receives requests from main.py, calculates damage/healing, and replies.

import zmq


# Calculate HP without letting it fall below 0 or exceed maximum HP.
def calculate_hp(request):
    try:
        current = request['current_hp']
        maximum = request['max_hp']
        amount = request['amount']
        action = request['action']
    except (KeyError, TypeError):
        return {'status': 'error', 'message': 'Missing HP information.'}

    # Check the data before doing any calculations.
    if type(current) != int or type(maximum) != int or type(amount) != int:
        return {'status': 'error', 'message': 'HP values must be whole numbers.'}
    if maximum <= 0 or current < 0 or current > maximum or amount <= 0:
        return {'status': 'error', 'message': 'Invalid HP values.'}

    if action == 'damage':
        new_hp = current - amount
        if new_hp < 0:
            new_hp = 0
    elif action == 'heal':
        new_hp = current + amount
        if new_hp > maximum:
            new_hp = maximum
    else:
        return {'status': 'error', 'message': 'Unknown action.'}

    return {'status': 'success', 'new_hp': new_hp}


# Keep listening for messages from the main program.
def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)  # REP means reply (server)
    socket.bind('tcp://127.0.0.1:5555')
    print('HP service is running. Press Ctrl+C to stop.')

    try:
        while True:
            request = socket.recv_json()  # Receive JSON from main.py
            response = calculate_hp(request)
            socket.send_json(response)    # Send the result back to main.py
    except KeyboardInterrupt:
        print('\nHP service stopped.')
    finally:
        socket.close(0)
        context.term()


if __name__ == '__main__':
    main()
