# satisfactory-bot
A Telegram bot to manage Docker images for a satisfactory dedicated server and post update news to Telegram.


> Satisfactory is a first-person open-world factory building game with a dash of exploration and combat. Play alone or with friends, explore an alien planet, create multi-story factories, and enter conveyor belt heaven!

This repository is in no way affiliated with the Satisfactory brand or Coffee Stain Studios. For information about the game refer to the [official website](https://www.satisfactorygame.com) or the [dedicated server documentation](https://satisfactory.fandom.com/wiki/Dedicated_servers). For issues with the game consult the [official help](https://questions.satisfactorygame.com/).

## Dedicated Server

This repository provides Docker images for all versions of the dedicated server that are available on Steam. New versions should be available 15-30 minutes after an official update was published on Steam.

| Game Version | Docker Image |
|--------------|--------------|
| Early Access | [server-public](https://github.com/ekeih/satisfactory-bot/pkgs/container/satisfactory-bot%2Fserver-public) |
| Experimental | [server-experimental](https://github.com/ekeih/satisfactory-bot/pkgs/container/satisfactory-bot%2Fserver-experimental) |

The images are tagged with the release date and the build ID, e.g. `2022.05.24-8719350`.

Following ports are exposed by the Docker images:
- 15777/udp
- 15000/udp
- 7777/udp

The game data is stored in `/home/steam/.config/Epic/FactoryGame/Saved/SaveGames/server`, make sure to mount a volume into the container at this path to persist your savegame.

## The Bot

If you only want to use the dedicated server to play Satisfactory, you do not need to use or run the bot yourself. Just use one of the existing images from above.

If you really want to run the bot, the easiest way is to fork this repository. Create a GitHub token that has write access to the fork and also create a Telegram bot token.

To run the bot you can either use the existing [bot image](https://github.com/ekeih/satisfactory-bot/pkgs/container/satisfactory-bot%2Fbot) or clone the repository, install the bot manually with `cd satisfactory-bot && pip install .`.

Then run the bot: `satisfactory-bot -b $telegram-bot-token -g $github-token -c $telegram-chat-id -r $github-repository`.

When the bot discovers a new release of the dedicated server it pushes a git tag to the repository which triggers a GitHub action to build a Docker images with the respective version.

## Credits

Thanks to [YannickFricke/Satisfactory-DS-Docker](https://github.com/YannickFricke/Satisfactory-DS-Docker) for the inspiration to automatically build Docker images for the dedicated server and the initial Dockerfile.

## License

The source code in this repository and the Docker image of the bot are licensed under the [MIT](./LICENSE) license. While building the server images proprietary content (`steamcmd` and the dedicated server) is downloaded and installed from Valve and Coffee Stain Studios.
