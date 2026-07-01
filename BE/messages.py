# messages.py
class Messages:
    @staticmethod
    def host_greetings():
        return """<frame><cmd><id>0</id><hostGreetings>
        <readerType>SIMATIC_RF615R</readerType>
        <supportedVersions><version>V3.1</version></supportedVersions>
        </hostGreetings></cmd></frame>"""

    @staticmethod
    def trigger(readpoint="Readpoint_L", triggerMode="Single"):
        return f"""<frame><cmd><id>0</id><triggerSource>
        <sourceName>{readpoint}</sourceName>
        <triggerMode>{triggerMode}</triggerMode>
        </triggerSource></cmd></frame>"""

    @staticmethod
    def heartbeat():
        return """<frame><cmd><id>99</id><heartBeat/></cmd></frame>"""