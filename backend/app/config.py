"""Configuration management for AgentLicense backend."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_env: str = "development"
    debug: bool = True
    demo_mode: bool = True

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = "sqlite:///./agentlicense.db"

    # ------------------------------------------------------------------
    # Algorand / x402 AVM
    # ------------------------------------------------------------------

    # Address that receives payments.
    # Required when using real x402 payments.
    avm_address: str = "ZGCL6MV4FEA7AP5NCD6UJQXD4L7VGWYWDHHYBGKXVMTTU4HQMPEFTWPQSY"

    # Private key is ONLY needed for the optional payer/demo client.
    # The server should normally NOT need the payer's private key.
    avm_private_key: str = ""

    # Algorand network.
    # Supported values for this project: testnet / mainnet
    algorand_network: str = "testnet"

    # Algod node used for blockchain queries/submission.
    algorand_algod_url: str = "https://testnet-api.algonode.cloud"

    # Indexer used for transaction/account lookups.
    algorand_indexer_url: str = "https://testnet-idx.algonode.cloud"

    # USDC ASA on the selected Algorand network.
    #
    # Algorand TestNet USDC:
    # 10458941
    #
    # Change this if you intentionally use another asset/network.
    algorand_asset_id: int = 10458941

    # x402 facilitator.
    x402_facilitator_url: str = "https://x402.org/facilitator"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def x402_configured(self) -> bool:
        """Whether the server has enough information for x402."""
        return bool(
            self.avm_address
            and self.x402_facilitator_url
            and self.algorand_network
        )

    @property
    def algorand_configured(self) -> bool:
        """Whether Algorand connection information is configured."""
        return bool(
            self.algorand_algod_url
            and self.algorand_indexer_url
            and self.algorand_asset_id
        )


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()