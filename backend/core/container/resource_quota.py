from typing import Dict, Any, Optional
import json
from kubernetes.client.rest import ApiException
from backend.core.container.client import get_kubernetes_client
from backend.core.logs.loguru_config import Logger
from backend.models.workspace import ResourceGroup

logger = Logger.get_logger()


class ResourceQuotaManager:
    """ResourceQuota管理器"""

    def __init__(self):
        self.k8s_client = get_kubernetes_client()

    def create_resource_quota(self,
                            name: str,
                            namespace: str,
                            hard_limits: Dict[str, str]
                ) -> Dict[str, Any]:
        """
        创建ResourceQuota

        Args:
            name: ResourceQuota名称
            namespace: 命名空间
            hard_limits: 资源限制

        Returns:
            ResourceQuota对象
        """
        try:
            resource_quota_body = {
                "apiVersion": "v1",
                "kind": "ResourceQuota",
                "metadata": {
                    "name": name,
                    "namespace": namespace
                },
                "spec": {
                    "hard": hard_limits
                }
            }

            result = self.k8s_client.core_v1_api.create_namespaced_resource_quota(
                namespace=namespace,
                body=resource_quota_body
            )
            logger.info(f"ResourceQuota {name} created in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to create ResourceQuota {name} in namespace {namespace}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while creating ResourceQuota {name} in namespace {namespace}: {e}")
            raise

    def update_resource_quota(self,
                            name: str,
                            namespace: str,
                            hard_limits: Dict[str, str]) -> Dict[str, Any]:
        """
        更新ResourceQuota

        Args:
            name: ResourceQuota名称
            namespace: 命名空间
            hard_limits: 资源限制

        Returns:
            ResourceQuota对象
        """
        try:
            resource_quota_body = {
                "apiVersion": "v1",
                "kind": "ResourceQuota",
                "metadata": {
                    "name": name,
                    "namespace": namespace
                },
                "spec": {
                    "hard": hard_limits
                }
            }

            result = self.k8s_client.core_v1_api.patch_namespaced_resource_quota(
                name=name,
                namespace=namespace,
                body=resource_quota_body
            )
            logger.info(f"ResourceQuota {name} updated in namespace {namespace}")
            return result
        except ApiException as e:
            logger.error(f"Failed to update ResourceQuota {name} in namespace {namespace}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating ResourceQuota {name} in namespace {namespace}: {e}")
            raise

    def delete_resource_quota(self, name: str, namespace: str) -> None:
        """
        删除ResourceQuota

        Args:
            name: ResourceQuota名称
            namespace: 命名空间
        """
        try:
            self.k8s_client.core_v1_api.delete_namespaced_resource_quota(
                name=name,
                namespace=namespace
            )
            logger.info(f"ResourceQuota {name} deleted from namespace {namespace}")
        except ApiException as e:
            if e.status != 404:
                logger.error(f"Failed to delete ResourceQuota {name} from namespace {namespace}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error while deleting ResourceQuota {name} from namespace {namespace}: {e}")
            raise

    def get_resource_quota(self, name: str, namespace: str) -> Dict[str, Any]:
        """
        获取ResourceQuota

        Args:
            name: ResourceQuota名称
            namespace: 命名空间

        Returns:
            ResourceQuota对象
        """
        try:
            result = self.k8s_client.core_v1_api.read_namespaced_resource_quota(
                name=name,
                namespace=namespace
            )
            return result
        except ApiException as e:
            logger.error(f"Failed to get ResourceQuota {name} from namespace {namespace}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting ResourceQuota {name} from namespace {namespace}: {e}")
            raise

    def list_resource_quotas(self, namespace: str) -> Dict[str, Any]:
        """
        列出命名空间中的所有ResourceQuota

        Args:
            namespace: 命名空间

        Returns:
            ResourceQuota列表
        """
        try:
            result = self.k8s_client.core_v1_api.list_namespaced_resource_quota(namespace=namespace)
            return result
        except ApiException as e:
            logger.error(f"Failed to list ResourceQuotas in namespace {namespace}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while listing ResourceQuotas in namespace {namespace}: {e}")
            raise

    def create_resource_quota_from_dict(self,
                                      name: str,
                                      namespace: str,
                                      quota_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        从字典创建ResourceQuota

        Args:
            name: ResourceQuota名称
            namespace: 命名空间
            quota_dict: 资源配额字典

        Returns:
            ResourceQuota对象
        """
        try:
            hard_limits = {}

            # 处理CPU资源
            if "cpu_limit" in quota_dict and quota_dict["cpu_limit"]:
                hard_limits["limits.cpu"] = quota_dict["cpu_limit"]
            if "cpu_request" in quota_dict and quota_dict["cpu_request"]:
                hard_limits["requests.cpu"] = quota_dict["cpu_request"]

            # 处理内存资源
            if "memory_limit" in quota_dict and quota_dict["memory_limit"]:
                hard_limits["limits.memory"] = quota_dict["memory_limit"]
            if "memory_request" in quota_dict and quota_dict["memory_request"]:
                hard_limits["requests.memory"] = quota_dict["memory_request"]

            # 处理存储资源
            if "storage_request" in quota_dict and quota_dict["storage_request"]:
                hard_limits["requests.storage"] = quota_dict["storage_request"]

            # 处理对象数量限制
            if "replicas" in quota_dict and quota_dict["replicas"]:
                hard_limits["count/deployments.apps"] = str(quota_dict["replicas"])
                hard_limits["count/services"] = str(quota_dict["replicas"] * 2)

            # 处理自定义资源
            if "custom_resources" in quota_dict and quota_dict["custom_resources"]:
                hard_limits.update(quota_dict["custom_resources"])

            return self.create_resource_quota(name, namespace, hard_limits)
        except Exception as e:
            logger.error(f"Failed to create ResourceQuota from dict: {e}")
            raise

    def get_namespace_resource_usage(self, namespace: str) -> Dict[str, Any]:
        """
        获取命名空间的资源使用情况

        Args:
            namespace: 命名空间

        Returns:
            资源使用情况
        """
        try:
            # 获取ResourceQuota状态
            quotas = self.list_resource_quotas(namespace)

            usage_info = {}
            for quota in quotas.items:
                quota_name = quota.metadata.name
                usage_info[quota_name] = {
                    "hard": {},
                    "used": {}
                }

                # 添加硬限制
                if quota.status.hard:
                    usage_info[quota_name]["hard"] = quota.status.hard

                # 添加已使用量
                if quota.status.used:
                    usage_info[quota_name]["used"] = quota.status.used

            return usage_info
        except Exception as e:
            logger.error(f"Failed to get resource usage for namespace {namespace}: {e}")
            raise

    def apply_resource_group_quota(self, resource_group: ResourceGroup, namespace: str) -> Dict[str, Any]:
        """
        为资源组在指定命名空间中应用资源配额

        Args:
            resource_group: 资源组对象
            namespace: 命名空间

        Returns:
            ResourceQuota对象
        """
        try:
            # 构建资源配额字典
            quota_dict = {
                "cpu_limit": resource_group.cpu_limit,
                "cpu_request": resource_group.cpu_request,
                "memory_limit": resource_group.memory_limit,
                "memory_request": resource_group.memory_request,
                "storage_request": resource_group.storage_request,
                "replicas": resource_group.replicas
            }

            # 处理自定义资源
            if resource_group.custom_resources:
                try:
                    quota_dict["custom_resources"] = json.loads(resource_group.custom_resources)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse custom resources for resource group {resource_group.id}")

            # 创建或更新ResourceQuota
            return self.create_resource_quota_from_dict(resource_group.name, namespace, quota_dict)
        except Exception as e:
            logger.error(f"Failed to apply resource group quota for {resource_group.code} in namespace {namespace}: {e}")
            raise

    def remove_resource_group_quota(self, resource_group: ResourceGroup, namespace: str) -> None:
        """
        从指定命名空间中移除资源组的资源配额

        Args:
            resource_group: 资源组对象
            namespace: 命名空间
        """
        try:
            self.delete_resource_quota(resource_group.name, namespace)
        except Exception as e:
            logger.error(f"Failed to remove resource group quota for {resource_group.name} in namespace {namespace}: {e}")
            raise


# 全局ResourceQuota管理器实例
_resource_quota_manager: Optional[ResourceQuotaManager] = None


def get_resource_quota_manager() -> ResourceQuotaManager:
    """
    获取ResourceQuota管理器实例（单例模式）

    Returns:
        ResourceQuotaManager实例
    """
    global _resource_quota_manager
    if _resource_quota_manager is None:
        _resource_quota_manager = ResourceQuotaManager()
    return _resource_quota_manager
