#!/bin/bash
# Exercise only the synthetic account created by this script.
set -euo pipefail
base=${1:-http://localhost:8080}
mkdir -p evidence
payload='{"name":"Capstone Demo","email":"capstone@example.com","address":"123 Test Street","phone_number":"555-0100","date_joined":"2026-11-03"}'
updated='{"name":"Capstone Updated","email":"capstone@example.com","address":"456 Test Street","phone_number":"555-0101","date_joined":"2026-11-03"}'
record() {
  local file=$1; shift
  { printf '$ '; printf '%q ' "$@"; printf '\n'; "$@"; printf '\n'; } > "evidence/$file.txt"
}
record rest-create-done curl -sS -i -X POST "$base/accounts" -H 'Content-Type: application/json' -d "$payload"
location=$(sed -n 's/^[Ll]ocation: //p' evidence/rest-create-done.txt | tr -d '\r')
test -n "$location"
record rest-list-done curl -sS -i "$base/accounts"
record rest-read-done curl -sS -i "$location"
record rest-update-done curl -sS -i -X PUT "$location" -H 'Content-Type: application/json' -d "$updated"
record rest-delete-done curl -sS -i -X DELETE "$location"
curl --fail -sS "$base/" > evidence/kube-app-output.txt
cat evidence/rest-create-done.txt evidence/rest-delete-done.txt
