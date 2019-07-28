from definitions import DATABASE_PATH
import peewee
import os

is_database_new = False
if not os.path.isfile(DATABASE_PATH):
    is_database_new = True

database = peewee.SqliteDatabase(DATABASE_PATH)


class BaseModel(peewee.Model):
    class Meta:
        database = database


class Contacts(BaseModel):
    name = peewee.CharField(unique=True)
    email = peewee.CharField(unique=True)

    @staticmethod
    def get_contacts():
        aDict = {}
        query1 = Contacts.select()
        for i in query1:
            aDict[i.name] = i.email

        return aDict


class SupportedApplications(BaseModel):
    app_name = peewee.CharField(unique=True)
    terminal_command = peewee.CharField()

    @staticmethod
    def add_entry(name, command):
        application = SupportedApplications(app_name=name,
                                            terminal_command=command)
        application.save()

    @staticmethod
    def remove_entry(name):
        print("remove entry")
        entry = SupportedApplications.get(SupportedApplications.app_name == name)
        entry.delete_instance()

    @staticmethod
    def edit_entry(old_name, new_name, command):
        entry = SupportedApplications.get(SupportedApplications.app_name == old_name)
        entry.app_name = new_name
        entry.terminal_command = command
        entry.save()

    # @staticmethod
    # def check_if_exists(app):
    #     query = SupportedApplications.select().where(CommandTriggers.app_name == app)
    #
    #     if query.exists():
    #         return app

class CommandTrigger(BaseModel):
    text_str = peewee.CharField(unique=True)

class CommandIdentifier(BaseModel):
    name = peewee.CharField(unique=True)

class Command(BaseModel):
    cmd_identifier = peewee.ForeignKeyField(CommandIdentifier)
    cmd_trigger = peewee.ForeignKeyField(CommandTrigger)

    @staticmethod
    def get_commands():
        array = []
        query1 = CommandIdentifier.select()
        for i in query1:
            array.append([i.name])

        query2 = Command.select().order_by(Command.cmd_identifier)

        array_length = len(array)
        for j in range(0, array_length):
            array2 = []
            for i in query2:
                if i.cmd_identifier.name == array[j][0]:
                    array2.append(i.cmd_trigger.text_str)
            array[j].append(array2)

        return array



def create_tables():
    with database:
        database.create_tables([SupportedApplications, CommandTrigger, CommandIdentifier, Command, Contacts])


def populate_tables():
    supported_applications = [
        {
            "app_name": "Kodi",
            "terminal_command": "kodi"
        },
        {
            "app_name": "Браузер",
            "terminal_command": "firefox"
        },
        {
            "app_name": "Блокнот",
            "terminal_command": "gedit"
        }
    ]

    for app in supported_applications:
        a = SupportedApplications(**app)
        a.save()

    data = (
        ('time', ('текущее время', 'сейчас времени', 'который час')),
        ('unread_email', ('непрочитанные сообщения', 'непрочитанная почта')),
        ('send_email', ('отправь письмо', 'отправь имейл', 'отправить имейл')),
        ('events_day', ('события сегодня', 'запланировано на день')),
        ('add_event', ('добавить событие', 'создать встречу')),
        ('weather', ('какая погода', 'с погодой')),
        ('help', ('могу сделать', 'твои функции', 'у тебя функции'))
    )

    for identifier, triggers in data:
        cmd_id = CommandIdentifier.create(name=identifier)
        for trigger in triggers:
            cmd_trgr = CommandTrigger.create(text_str=trigger)
            Command.create(cmd_identifier=cmd_id, cmd_trigger=cmd_trgr)


if is_database_new is True:
    create_tables()
    populate_tables()

if __name__ == '__main__':
    print(Contacts.get_contacts())