# Tasks

<!-- Group tasks by code repo in integration order (.mra-flow/bin/mra-repo list: dependencies first). [<key>] is a repo key from mra-flow.toml -->

## 1. <key>: <!-- Task Group Name -->

- [ ] 1.1 [<key>] <!-- Task description, including how to verify it -->
  Covers: <!-- Requirement / Scenario -->
- [ ] 1.2 [<key>] <!-- Task description -->
  Depends on: 1.1

## 2. <dependent key>: <!-- Task Group Name -->

- [ ] 2.1 [<dependent key>] <!-- Task description -->
  Depends on: 1.1
  Covers: <!-- Requirement / Scenario -->

## 3. Integration

<!-- Only when a contract is involved -->

- [ ] 3.1 [<dependent key>] <!-- End-to-end verification across the contract -->
  Depends on: 1.2, 2.1
