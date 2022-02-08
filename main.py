import os

from aonprd_grabber import AonprdGrabber

if __name__ == '__main__':
    grabber = AonprdGrabber()
    letters = grabber.get_creatures()
    try:
        os.mkdir('creatures')
    except FileExistsError as exc:
        print(exc)

    for letter in letters:
        data = letters[letter]
        path = f'creatures/{letter}'
        print(f'Start parsing creatures for letter {letter}. There are {len(data)} creatures')

        try:
            os.mkdir(path)
        except FileExistsError as exc:
            print(exc)

        for creature in data:
            grabber.save_creature(path, creature)
