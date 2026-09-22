# shellcheck shell=bash
rr() {
  local project="${RR_DEFAULT_PROJECT:-}"
  local remote_host="${RR_REMOTE_HOST:-}"
  local remote_project_root="${RR_REMOTE_PROJECT_ROOT:-}"
  local remote_root
  local dry_run=false
  local -a files deleted_files unique_files normalized_files
  local -A seen
  local f repo_root absolute_file relative_file

  while (( $# )); do
    case "$1" in
      -p|--project)
        [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; return 2; }
        project="$2"
        shift 2
        ;;
      --dry-run)
        dry_run=true
        shift
        ;;
      --)
        shift
        files+=("$@")
        break
        ;;
      -*)
        echo "Unknown option: $1" >&2
        return 2
        ;;
      *)
        files+=("$1")
        shift
        ;;
    esac
  done


  if ! repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "Git working tree required" >&2
    return 2
  fi

  for f in "${files[@]}"; do
    absolute_file="${f:A}"
    if [[ "$absolute_file" != "$repo_root" && "$absolute_file" != "$repo_root/"* ]]; then
      echo "File is outside Git working tree: $f" >&2
      return 2
    fi
    if [[ "$absolute_file" == "$repo_root" ]]; then
      relative_file="."
    else
      relative_file="${absolute_file#"$repo_root/"}"
    fi
    normalized_files+=("$relative_file")
  done
  files=("${normalized_files[@]}")

  for f in "${files[@]}"; do
    if [[ -z "${seen[$f]-}" ]]; then
      unique_files+=("$f")
      seen[$f]=1
    fi
  done
  files=("${unique_files[@]}")

  if [[ -z "$project" || -z "$remote_host" || -z "$remote_project_root" ]]; then
    echo "Configuration required: RR_DEFAULT_PROJECT, RR_REMOTE_HOST, and RR_REMOTE_PROJECT_ROOT" >&2
    return 2
  fi
  if [[ "$project" == "." || "$project" == ".." || "$project" == *[^A-Za-z0-9._-]* ]]; then
    echo "Invalid project name: $project" >&2
    return 2
  fi

  remote_root="${remote_project_root%/}/$project"

  if (( ${#files[@]} == 0 )); then
    echo "📦 No files args → using git status..."
    local entry git_state file_path
    while IFS= read -r -d '' entry; do
      git_state="${entry[1,2]}"
      file_path="${entry[4,-1]}"
      if [[ "$git_state" == *R* || "$git_state" == *C* ]]; then
        IFS= read -r -d '' || return 2
      fi
      if [[ "$git_state" == *D* ]]; then
        deleted_files+=("$file_path")
        continue
      fi
      if [[ -z "${seen[$file_path]-}" ]]; then
        files+=("$file_path")
        seen[$file_path]=1
      fi
    done < <(git status --porcelain=v1 -z --untracked-files=all)

    if (( ${#deleted_files[@]} )); then
      echo "Deleted files are reported but not removed remotely:"
      printf ' - %s\n' "${deleted_files[@]}"
    fi
    if (( ${#files[@]} == 0 )); then
      echo "✅ Nothing to sync"
      return 0
    fi
  fi

  echo "📁 Project: $project"
  echo "📋 Files to sync to $project:"
  for f in "${files[@]}"; do
    echo " - $f"
  done

  if [[ "$dry_run" == true ]]; then
    echo "Dry run: no files transferred"
    return 0
  fi

  printf '\n🚀 Proceed with rsync to %s? (y/N): ' "$project"
  local confirm
  IFS= read -r confirm

  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "❌ Cancelled"
    return 0
  fi

  for f in "${files[@]}"; do
    local source_file="$repo_root/$f"
    if [ ! -e "$source_file" ]; then
      echo "⚠️ Missing: $f"
      continue
    fi

    local remote_destination
    printf -v remote_destination '%q' "$remote_root/$f"
    if [ -d "$source_file" ]; then
      if ! rsync -avz -- "${source_file%/}/" "$remote_host:$remote_destination"; then
        echo "❌ rsync failed: $f" >&2
        return 1
      fi
    else
      if ! rsync -avz -- "$source_file" "$remote_host:$remote_destination"; then
        echo "❌ rsync failed: $f" >&2
        return 1
      fi
    fi
  done

  echo "✅ Done"
}
