from backend.core.container.client import get_kubernetes_client



client = get_kubernetes_client(in_cluster=False)



client.update_namespace(name="ws-385b3205", labels={"app": "prod"})
