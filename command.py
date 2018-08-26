# coding=utf-8
import collections
import re
import vlc

from embedbuilder import EmbedBuilder


class Command:
    def __init__(self):
        self.command_dict = collections.OrderedDict()
        self.command_dict['/tableflip'] = {'cmd': self.shoo, 'params': None,
                                        'description': "Shoo away cat."}
        self.command_dict[u'(╯°□°）╯︵'] = self.command_dict['/tableflip']

    def parse_command(self, string):
        parts = re.split('\s+', string)
        command = self.command_dict.get(parts[0])
        if command is None:
            if parts[0].lower() == "help":
                return self.help()
            return None, None

        if command.get('params'):
            return command['cmd'](parts)
        else:
            return command['cmd']()

    def help(self):
        builder = EmbedBuilder()
        builder.set_title('Commands, Parameters and Description')

        for command, details in self.command_dict.items():
            builder.add_field(title='%s %s' % (command, details.get('params') or ''),
                              text=details.get('description'))

        return None, builder.get_embeds()

    def shoo(self):
        p = vlc.MediaPlayer("SCREAM_4.mp3")
        p.play()
        return None, None