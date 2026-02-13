"""
Rate limiter module, this class is used to manage the
rate of requests to the target website to avoid rate
limiting and blocking.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RatePolicy:
	min_delay_s: float = 2.0
	max_delay_s: float = 6.0
	min_jitter_s: float = 0.0
	max_jitter_s: float = 4.0


@dataclass(frozen=True)
class RetryPolicy:
	base_delay_s: float = 10.0
	max_delay_s: float = 20.0
	min_jitter_s: float = 0.0
	max_jitter_s: float = 4.0


class RateLimiter:
	def __init__(
		self,
		rate: RatePolicy,
		retry: RetryPolicy,
		*,
		retry_requests: int = 10,
		retry_cooldown_s: float = 180.0,
	) -> None:
		self._rate = rate
		self._retry = retry
		self._retry_requests = retry_requests
		self._retry_cooldown_s = retry_cooldown_s

		self._lock = asyncio.Lock()

		self._next_slot_ts = 0.0

		self._in_backoff = False
		self._retry_left = 0
		self._cooldown_pending = False

	def enter_backoff(self) -> None:
		self._in_backoff = True
		self._retry_left = self._retry_requests
		self._cooldown_pending = True

	async def wait_turn(self) -> None:
		sleep_s = 0.0

		async with self._lock:
			now = time.monotonic()

			slot_ts = max(now, self._next_slot_ts)

			if self._in_backoff and self._cooldown_pending:
				slot_ts = max(
					slot_ts,
					now + self._retry_cooldown_s,
				)
				self._cooldown_pending = False

			delay_s = self._pick_delay()

			self._next_slot_ts = slot_ts + delay_s

			sleep_s = max(0.0, slot_ts - now)
			logger.info(
				f'RateLimiter: sleeping for {sleep_s:.2f}s'
				f' (backoff={self._in_backoff},'
				f' retry_left={self._retry_left})'
			)

			self._consume_retry()

		if sleep_s > 0:
			await asyncio.sleep(sleep_s)

	def _pick_delay(self) -> float:
		if self._in_backoff:
			base = self._retry.base_delay_s
			jit = self._pick_jitter(
				self._retry.min_jitter_s,
				self._retry.max_jitter_s,
			)
			raw = base + jit
			return min(raw, self._retry.max_delay_s)

		base = random.uniform(
			self._rate.min_delay_s,
			self._rate.max_delay_s,
		)
		jit = self._pick_jitter(
			self._rate.min_jitter_s,
			self._rate.max_jitter_s,
		)
		return base + jit

	def _pick_jitter(self, lo: float, hi: float) -> float:
		if hi <= lo:
			return lo
		return random.uniform(lo, hi)

	def _consume_retry(self) -> None:
		if not self._in_backoff:
			return

		if self._retry_left > 0:
			self._retry_left -= 1

		if self._retry_left <= 0:
			self._in_backoff = False
			self._cooldown_pending = False
