import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# import model
from src.model.datamanager import SupportedApplications

# DBus
from pydbus import SessionBus
import threading


class DBusService(object):
    """
        <node>
            <interface name='org.LinuxAssistantClient'>
                <method name='probe_connection'>
                    <arg type='b' name='response' direction='out'/>
                </method>
                <method name='print_text'>
                     <arg type='s' name='text' direction='in'/>
                      <arg type='b' name='is_user' direction='in'/>
                </method>
                <method name='echo_string'>
                    <arg type='s' name='a' direction='in'/>
                    <arg type='s' name='response' direction='out'/>
                </method>
                <method name='quit'/>
            </interface>
        </node>
    """

    def probe_connection(self):
        return True

    def print_text(self, text, is_user):
        print("Print text")
        if is_user is True:
            add_row(text, "right")
        else:
            add_row(text, "left")

    def echo_string(self, s):
        """returns whatever is passed to it"""
        return s


class Handler:
    def add_app_button_clicked(self, *args):
        print("Add command")
        add_app_dialog.show_all()
        response = add_app_dialog.run()

        name_entry = builder.get_object("add_app_name_entry")
        command_entry = builder.get_object("add_command_entry")

        if response == -10:
            print("Apply")
            SupportedApplications.add_entry(name_entry.get_text(), command_entry.get_text())
            draw_table(True)
            name_entry.set_text("")
            command_entry.set_text("")

    def edit_app_button_clicked(self, *args):
        print("edit command")
        name_entry = builder.get_object("edit_app_name_entry")
        command_entry = builder.get_object("edit_command_entry")

        (model, iter) = select.get_selected()
        print((model[iter][0]))
        name_entry.set_text((model[iter][0]))
        command_entry.set_text((model[iter][1]))

        edit_app_dialog.show_all()
        response = edit_app_dialog.run()

        if response == -10:
            print("Apply")
            SupportedApplications.edit_entry((model[iter][0]), name_entry.get_text(), command_entry.get_text())
            draw_table(True)
            name_entry.set_text("")
            command_entry.set_text("")

    def remove_app_button_clicked(self, *args):
        print("remove command")
        (model, iter) = select.get_selected()
        SupportedApplications.remove_entry((model[iter][0]))
        draw_table(True)

    def on_record_button_clicked(self, *args):
        thread = threading.Thread(target=server.wakeup_call)
        thread.daemon = True
        thread.start()


    def on_dialog_delete_event(self, dialog, event):
        dialog.hide()
        return True

    def on_response(self, dialog, response_id):
        dialog.hide()

    def on_tree_selection_changed(selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            print("You selected", model[treeiter][0])

    def main_window_destroy(self, *args):
        Gtk.main_quit()


def get_app_list_store():
    store = Gtk.ListStore(str, str)
    app_list = SupportedApplications.select().order_by(SupportedApplications.app_name)
    for app in app_list:
        store.append([app.app_name, app.terminal_command])
    return store


# def draw_table(redraw=False):
#     store = get_app_list_store()
#
#     app_list_treeview.set_model(store)
#
#     renderer = Gtk.CellRendererText()
#
#     if not redraw:
#         column_app = Gtk.TreeViewColumn("Приложение", renderer, text=0)
#         app_list_treeview.append_column(column_app)
#
#         column_command = Gtk.TreeViewColumn("Команда", renderer, text=1)
#         app_list_treeview.append_column(column_command)


def add_row(text, text_alignment):
    row = Gtk.ListBoxRow()
    gtkbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    row.add(gtkbox)

    if text_alignment is "right":
        message = Gtk.Label(text, xalign=1)
    elif text_alignment is "left":
        message = Gtk.Label(text, xalign=0)

    gtkbox.pack_start(message, True, True, 0)
    assistant_listbox.add(row)
    assistant_listbox.show_all()


if __name__ == '__main__':

    builder = Gtk.Builder()
    builder.add_from_file("client1.glade")
    builder.connect_signals(Handler())

    main_window = builder.get_object("main_window")
    # add_app_dialog = builder.get_object("add_app_dialog")
    # edit_app_dialog = builder.get_object("edit_app_dialog")
    # app_list_treeview = builder.get_object("app_list_treeview")
    server_status_label = builder.get_object("server_status_label")
    assistant_listbox = builder.get_object("assistant_listbox")

    # select = app_list_treeview.get_selection()
    # select.connect("changed", Handler.on_tree_selection_changed)

    # draw_table()

    client_bus = SessionBus()
    client_bus.publish("org.LinuxAssistantClient", DBusService())

    server_bus = SessionBus()
    is_server_running = False

    try:
        server = server_bus.get("org.LinuxAssistantServer")
        is_server_running = server.client_init()
    except:
        print("Server is not running")

    if is_server_running is True:
        server_status_label.set_text("Server is running")
    else:
        server_status_label.set_text("Server is not running")

    main_window.show_all()

    Gtk.main()
