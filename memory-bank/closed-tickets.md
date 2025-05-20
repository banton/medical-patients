# Closed Tickets

This file tracks completed tickets, their resolution details, and any lessons learned.

---

__Ticket ID:__ SEC-001 (Corresponds to Task 4.1.1) __Title:__ Security - Fix Encryption Salt in `formatter.py`
__Epic:__ 4.1 Address Remaining Technical Debt
__Description:__ Implemented unique salt generation using PBKDF2 for encryption in `formatter.py`, enhancing security.
__Acceptance Criteria:__
1. `formatter.py` uses PBKDF2 for key derivation for AES encryption.
2. Each encryption operation uses a unique salt, stored alongside the ciphertext or derived in a reconstructible way if not stored.
3. The `encrypt_data` function in `formatter.py` correctly implements this.
4. Security of stored encrypted data is improved by preventing rainbow table attacks facilitated by a fixed salt.
__Status:__ Completed
__Branch:__ `feature/SEC-001-encryption-salt-fix` (example branch name)
__Date Completed:__ 2025-05-20
__PR/Commit Reference:__ Changes committed on May 20, 2025, as part of Phase 4.1.1 completion.
__Test Results Summary:__ Verified functionality; encryption and decryption successful with new salt mechanism.

---

__Ticket ID:__ UI-001 (Corresponds to Task 4.1.5) __Title:__ UI Refinement - Nationality Distribution in Front Editor
__Epic:__ 4.1 Address Remaining Technical Debt
__Description:__ Modified `FrontEditor.tsx` (within `ConfigurationPanel.tsx`) to use an ordered list of dropdowns for nationality distribution per front, improving usability and data structure. Ensured at least one nationality is always present. Backend Pydantic schemas (`schemas_config.py`) and an Alembic migration marker were updated accordingly.
__Acceptance Criteria:__
1. `FrontEditor.tsx` component in `ConfigurationPanel.tsx` uses an ordered list of dropdowns for selecting nationalities and their ratios for a front.
2. The UI ensures that at least one nationality is always selected for a front.
3. The data structure for nationality distribution sent to the backend is an ordered list (e.g., `List[Tuple[str, float]]`).
4. Backend Pydantic schemas in `patient_generator/schemas_config.py` (e.g., `FrontConfig`) are updated to reflect the new ordered list structure for nationality distribution.
5. An Alembic migration marker or necessary schema changes were made if database storage of this structure was affected.
__Status:__ Completed
__Branch:__ `feature/UI-001-nationality-dropdowns` (example branch name)
__Date Completed:__ 2025-05-20
__PR/Commit Reference:__ Changes committed on May 20, 2025, as part of Phase 4.1.5 completion.
__Test Results Summary:__ UI functionality verified; configuration saves and loads correctly with the new nationality distribution format.

---

__Ticket ID:__ UI-002 (Corresponds to Task 4.1.6) __Title:__ UI Refinement - Injury Distribution and Error Handling in Configuration Panel
__Epic:__ 4.1 Address Remaining Technical Debt
__Description:__ The injury distribution input in `ConfigurationPanel.tsx` was reverted to use three fixed categories ("Battle Injury", "Disease", "Non-Battle Injury") and their percentages, matching the simpler model previously in `static/index.html`. Backend Pydantic schemas (`schemas_config.py`) were updated to expect `injury_distribution` as `Dict[str, float]` with these fixed keys. Facility ID submission was corrected, and basic API error display remains.
__Acceptance Criteria:__
1. `ConfigurationPanel.tsx` presents inputs for "Battle Injury", "Disease", and "Non-Battle Injury" percentages.
2. The sum of these percentages is validated (e.g., to ensure it's 100%).
3. Backend Pydantic schemas in `patient_generator/schemas_config.py` (e.g., `ScenarioConfig` or equivalent) expect `injury_distribution` as a `Dict[str, float]` with keys "Battle Injury", "Disease", "Non-Battle Injury".
4. Submission of facility IDs from the configuration panel is correct.
5. Basic API error messages are displayed to the user in the configuration panel.
__Status:__ Completed
__Branch:__ `feature/UI-002-injury-dist-revert` (example branch name)
__Date Completed:__ 2025-05-20
__PR/Commit Reference:__ Changes committed on May 20, 2025, as part of Phase 4.1.6 completion.
__Test Results Summary:__ UI functionality for injury distribution verified; configurations save and load correctly. Basic error display confirmed.

---

__Ticket ID:__ DB-001 (Corresponds to Task 4.1.7) __Title:__ Database Fix - `parent_config_id` Usage for Configuration Versioning
__Epic:__ 4.1 Address Remaining Technical Debt
__Description:__ Corrected `parent_config_id` usage (was `parent_id`) in `patient_generator/database.py` SQL queries to ensure accurate linking for configuration versioning. This followed the successful application of Alembic migration `2b84a220e9ac_add_version_and_parent_to_config_template.py` which added `version` and `parent_config_id` columns to the `configuration_templates` table.
__Acceptance Criteria:__
1. SQL queries in `patient_generator/database.py` related to configuration template versioning (saving/loading versions) use the `parent_config_id` column name.
2. Creating a new version of a configuration template correctly links to its parent via `parent_config_id`.
3. Retrieval of configuration versions and their history is accurate.
4. Alembic migration `2b84a220e9ac` must have been successfully applied as a prerequisite.
__Status:__ Completed
__Branch:__ `feature/DB-001-parent-config-fix` (example branch name)
__Date Completed:__ 2025-05-20
__PR/Commit Reference:__ Changes committed on May 20, 2025, as part of Phase 4.1.7 completion.
__Test Results Summary:__ Configuration versioning functionality verified; parent-child relationships between configuration versions are correctly established and retrieved.
---
