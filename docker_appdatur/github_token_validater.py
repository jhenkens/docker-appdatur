import hashlib
import hmac


class GithubTokenValidater:
    def __init__(self, secret_token: str) -> None:
        self.secret_token = secret_token

    def generate_signature(self, payload_body: str) -> str:
        hash_object = hmac.new(
            self.secret_token.encode("utf-8"),
            msg=payload_body.encode(),
            digestmod=hashlib.sha256,
        )
        return "sha256=" + hash_object.hexdigest()

    def verify_signature(self, payload_body: str, signature_header: str) -> None:
        """Verify that the payload was sent from GitHub by validating SHA256.

        Raise and return 403 if not authorized.

        Args:
            payload_body: original request body to verify (request.body())
            signature_header: header received from GitHub (x-hub-signature-256)
        """
        if not signature_header:
            raise ValueError("x-hub-signature-256 header is missing!")

        expected_signature = self.generate_signature(payload_body)
        if not hmac.compare_digest(expected_signature, signature_header):
            raise ValueError("Request signatures didn't match!")
