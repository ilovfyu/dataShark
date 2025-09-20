





class ConfigHandler:


    @staticmethod
    async def k8s_handler(config: dict, tag: str):

        match tag:
            case "labels":
                return config.get("labels", {})
            case _:
                return ""