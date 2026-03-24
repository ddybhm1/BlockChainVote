"""IPFS 服务 - 通过 Pinata API 上传文件到 IPFS"""
import time
import requests
from config import PINATA_API_KEY, PINATA_SECRET_KEY, PINATA_TIMEOUT_SECONDS

PINATA_PIN_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"


def _get_headers():
    return {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY,
    }


def pin_file_to_ipfs(file_bytes: bytes, filename: str) -> str:
    """将文件上传到 Pinata 并 pin 到 IPFS，返回 CID"""
    if not PINATA_API_KEY or not PINATA_SECRET_KEY:
        raise RuntimeError("Pinata API 密钥未配置，请在 .env 中设置 PINATA_API_KEY 和 PINATA_SECRET_KEY")

    last_err = None
    for attempt in range(3):
        try:
            resp = requests.post(
                PINATA_PIN_URL,
                files={"file": (filename, file_bytes)},
                headers=_get_headers(),
                timeout=PINATA_TIMEOUT_SECONDS,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Pinata 上传失败: {resp.status_code} {resp.text}")
            return resp.json()["IpfsHash"]
        except requests.Timeout:
            last_err = RuntimeError(
                f"Pinata 上传超时（>{PINATA_TIMEOUT_SECONDS}s），请检查网络或稍后重试"
            )
        except requests.RequestException as e:
            last_err = RuntimeError(f"Pinata 网络请求失败: {str(e)}")
        except RuntimeError as e:
            # 认证失败等业务错误无需重试
            raise e

        # 仅网络类错误重试，做短暂退避
        if attempt < 2:
            time.sleep(1 + attempt)

    raise last_err or RuntimeError("Pinata 上传失败")


def pin_json_to_ipfs(json_data: dict, name: str = "metadata") -> str:
    """将 JSON 元数据上传到 Pinata，返回 CID"""
    if not PINATA_API_KEY or not PINATA_SECRET_KEY:
        raise RuntimeError("Pinata API 密钥未配置")

    payload = {
        "pinataContent": json_data,
        "pinataMetadata": {"name": name},
    }

    try:
        resp = requests.post(
            PINATA_JSON_URL,
            json=payload,
            headers={**_get_headers(), "Content-Type": "application/json"},
            timeout=PINATA_TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        raise RuntimeError(f"Pinata JSON 上传超时（>{PINATA_TIMEOUT_SECONDS}s）")
    except requests.RequestException as e:
        raise RuntimeError(f"Pinata JSON 网络请求失败: {str(e)}")

    if resp.status_code != 200:
        raise RuntimeError(f"Pinata JSON 上传失败: {resp.status_code} {resp.text}")

    return resp.json()["IpfsHash"]
