from typing import Optional, Dict, Any, List
from kubernetes import client, config
from kubernetes.client import V1Namespace
from kubernetes.client.rest import ApiException
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()


class KubernetesClient:
    """Kubernetes 客户端封装"""

    def __init__(self, in_cluster: bool = True):
        """
        初始化 Kubernetes 客户端

        Args:
            in_cluster: 是否在集群内运行
        """
        try:
            if in_cluster:
                # 在集群内运行，使用 ServiceAccount
                config.load_incluster_config()
            else:
                # 在集群外运行，使用 kubeconfig
                config.load_kube_config()

            self.core_v1_api = client.CoreV1Api()
            self.apps_v1_api = client.AppsV1Api()
            self.custom_objects_api = client.CustomObjectsApi()
            self.batch_v1_api = client.BatchV1Api()
            self.networking_v1_api = client.NetworkingV1Api()

            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def create_namespace(self, name: str, labels: Optional[Dict[str, str]] = None) -> client.V1Namespace:
        """
        创建命名空间

        Args:
            name: 命名空间名称
            labels: 标签

        Returns:
            V1Namespace 对象
        """
        try:
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=name,
                    labels=labels or {}
                )
            )
            result = self.core_v1_api.create_namespace(namespace)
            logger.info(f"Namespace {name} created successfully")
            return result
        except ApiException as e:
            logger.error(f"Failed to create namespace {name}: {e}")
            raise

    def delete_namespace(self, name: str) -> None:
        """
        删除命名空间

        Args:
            name: 命名空间名称
        """
        try:
            self.core_v1_api.delete_namespace(name)
            logger.info(f"Namespace {name} deleted successfully")
        except ApiException as e:
            logger.error(f"Failed to delete namespace {name}: {e}")
            raise

    def create_deployment(self, namespace: str, deployment_spec: Dict[str, Any]) -> client.V1Deployment:
        """
        创建 Deployment

        Args:
            namespace: 命名空间
            deployment_spec: Deployment 规格

        Returns:
            V1Deployment 对象
        """
        try:
            deployment = client.V1Deployment(**deployment_spec)
            result = self.apps_v1_api.create_namespaced_deployment(
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Deployment created in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to create deployment: {e}")
            raise

    def update_deployment(self, name: str, namespace: str, deployment_spec: Dict[str, Any]) -> client.V1Deployment:
        """
        更新 Deployment

        Args:
            name: Deployment 名称
            namespace: 命名空间
            deployment_spec: Deployment 规格

        Returns:
            V1Deployment 对象
        """
        try:
            deployment = client.V1Deployment(**deployment_spec)
            result = self.apps_v1_api.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Deployment {name} updated in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to update deployment {name}: {e}")
            raise

    def delete_deployment(self, name: str, namespace: str) -> None:
        """
        删除 Deployment

        Args:
            name: Deployment 名称
            namespace: 命名空间
        """
        try:
            self.apps_v1_api.delete_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deployment {name} deleted from namespace {namespace}")
        except ApiException as e:
            logger.error(f"Failed to delete deployment {name}: {e}")
            raise

    def get_deployment(self, name: str, namespace: str) -> client.V1Deployment:
        """
        获取 Deployment

        Args:
            name: Deployment 名称
            namespace: 命名空间

        Returns:
            V1Deployment 对象
        """
        try:
            result = self.apps_v1_api.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            return result
        except ApiException as e:
            logger.error(f"Failed to get deployment {name}: {e}")
            raise

    def list_deployments(self, namespace: str) -> List[client.V1Deployment]:
        """
        列出命名空间中的所有 Deployment

        Args:
            namespace: 命名空间

        Returns:
            Deployment 列表
        """
        try:
            result = self.apps_v1_api.list_namespaced_deployment(namespace=namespace)
            return result.items
        except ApiException as e:
            logger.error(f"Failed to list deployments in namespace {namespace}: {e}")
            raise

    def create_service(self, namespace: str, service_spec: Dict[str, Any]) -> client.V1Service:
        """
        创建 Service

        Args:
            namespace: 命名空间
            service_spec: Service 规格

        Returns:
            V1Service 对象
        """
        try:
            service = client.V1Service(**service_spec)
            result = self.core_v1_api.create_namespaced_service(
                namespace=namespace,
                body=service
            )
            logger.info(f"Service created in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to create service: {e}")
            raise

    def delete_service(self, name: str, namespace: str) -> None:
        """
        删除 Service

        Args:
            name: Service 名称
            namespace: 命名空间
        """
        try:
            self.core_v1_api.delete_namespaced_service(
                name=name,
                namespace=namespace
            )
            logger.info(f"Service {name} deleted from namespace {namespace}")
        except ApiException as e:
            logger.error(f"Failed to delete service {name}: {e}")
            raise

    def create_custom_resource(self,
                              group: str,
                              version: str,
                              namespace: str,
                              plural: str,
                              body: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建自定义资源

        Args:
            group: API 组
            version: API 版本
            namespace: 命名空间
            plural: 复数形式
            body: 资源定义

        Returns:
            创建的资源对象
        """
        try:
            result = self.custom_objects_api.create_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                body=body
            )
            logger.info(f"Custom resource created in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to create custom resource: {e}")
            raise

    def update_custom_resource(self,
                              group: str,
                              version: str,
                              namespace: str,
                              plural: str,
                              name: str,
                              body: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新自定义资源

        Args:
            group: API 组
            version: API 版本
            namespace: 命名空间
            plural: 复数形式
            name: 资源名称
            body: 资源定义

        Returns:
            更新的资源对象
        """
        try:
            result = self.custom_objects_api.patch_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=name,
                body=body
            )
            logger.info(f"Custom resource {name} updated in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to update custom resource {name}: {e}")
            raise

    def delete_custom_resource(self,
                              group: str,
                              version: str,
                              namespace: str,
                              plural: str,
                              name: str) -> None:
        """
        删除自定义资源

        Args:
            group: API 组
            version: API 版本
            namespace: 命名空间
            plural: 复数形式
            name: 资源名称
        """
        try:
            self.custom_objects_api.delete_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=name
            )
            logger.info(f"Custom resource {name} deleted from namespace {namespace}")
        except ApiException as e:
            logger.error(f"Failed to delete custom resource {name}: {e}")
            raise

    def get_custom_resource(self,
                           group: str,
                           version: str,
                           namespace: str,
                           plural: str,
                           name: str) -> Dict[str, Any]:
        """
        获取自定义资源

        Args:
            group: API 组
            version: API 版本
            namespace: 命名空间
            plural: 复数形式
            name: 资源名称

        Returns:
            资源对象
        """
        try:
            result = self.custom_objects_api.get_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=name
            )
            return result
        except ApiException as e:
            logger.error(f"Failed to get custom resource {name}: {e}")
            raise

    def list_custom_resources(self,
                             group: str,
                             version: str,
                             namespace: str,
                             plural: str) -> Dict[str, Any]:
        """
        列出自定义资源

        Args:
            group: API 组
            version: API 版本
            namespace: 命名空间
            plural: 复数形式

        Returns:
            资源列表
        """
        try:
            result = self.custom_objects_api.list_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural
            )
            return result
        except ApiException as e:
            logger.error(f"Failed to list custom resources: {e}")
            raise

    def update_namespace(self, name: str, labels: Optional[Dict[str, str]] = None,
                         annotations: Optional[Dict[str, str]] = None) -> client.V1Namespace:
        """
        更新命名空间，直接替换标签和注解

        Args:
            name: 命名空间名称
            labels: 标签
                - 传入 None 时，不修改现有标签
                - 传入空字典 {} 时，删除所有现有标签
                - 传入具体标签时，直接替换所有现有标签
            annotations: 注解
                - 传入 None 时，不修改现有注解
                - 传入空字典 {} 时，删除所有现有注解
                - 传入具体注解时，直接替换所有现有注解

        Returns:
            V1Namespace 对象
        """
        ## 清除现有注解 todo: 无法直接覆盖注解

        try:
            update_model = {
                'metadata': {
                    'labels': None,
                },
                'name': name
            }
            self.core_v1_api.patch_namespace(name=name, body=update_model)
            # 构建要更新的元数据
            metadata = client.V1ObjectMeta()
            if labels is not None:
                metadata.labels = labels
                metadata.name = name
            if annotations is not None:
                metadata.annotations = annotations
                metadata.name = name

            # 创建命名空间对象用于更新
            namespace = client.V1Namespace(
                metadata=metadata
            )

            # 如果没有需要更新的内容，直接返回现有的命名空间
            if not metadata.labels and not metadata.annotations:
                result = self.core_v1_api.read_namespace(name=name)
                logger.info(f"No updates needed for namespace {name}, returning existing namespace")
                return result

            # 使用 patch 方法更新命名空间
            result = self.core_v1_api.patch_namespace(
                name=name,
                body=namespace
            )
            logger.info(f"Namespace {name} updated successfully. Labels: {labels}, Annotations: {annotations}")
            return result
        except ApiException as e:
            logger.error(f"Failed to update namespace {name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating namespace {name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating namespace {name}: {e}")
            raise





# 全局客户端实例
_k8s_client: Optional[KubernetesClient] = None


def get_kubernetes_client(in_cluster: bool = True) -> KubernetesClient:
    """
    获取 Kubernetes 客户端实例（单例模式）

    Args:
        in_cluster: 是否在集群内运行

    Returns:
        KubernetesClient 实例
    """
    global _k8s_client
    if _k8s_client is None:
        _k8s_client = KubernetesClient(in_cluster=in_cluster)
    return _k8s_client


def init_kubernetes_client(in_cluster: bool = True) -> None:
    """
    初始化 Kubernetes 客户端

    Args:
        in_cluster: 是否在集群内运行
    """
    global _k8s_client
    _k8s_client = KubernetesClient(in_cluster=in_cluster)
