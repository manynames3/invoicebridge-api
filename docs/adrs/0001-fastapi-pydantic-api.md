# ADR 0001: Use FastAPI With Pydantic Contracts

## Status

Accepted

## Context

The API needs clear request/response contracts, OpenAPI docs, input validation, and a small amount of authentication and middleware. The project should be easy to review and run locally.

## Decision

Use FastAPI for HTTP routing and OpenAPI generation, with Pydantic v2 models for normalized invoice inputs and structured responses.

## Consequences

- Endpoint contracts are visible in `/docs`.
- Validation, transform, send, status, and audit responses are typed and testable.
- Business validation still lives in service validators, not only in Pydantic field validation, so the API can return machine-readable compliance errors.
