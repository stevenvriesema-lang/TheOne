"""Simple CLI to view and manage assistant memory.

Usage:
  python tools/memory_cli.py view
  python tools/memory_cli.py set name Sefer
  python tools/memory_cli.py delete name
  python tools/memory_cli.py clear
"""
import argparse
from core import memory
import json


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('view')
    pset = sub.add_parser('set')
    pset.add_argument('key')
    pset.add_argument('value')
    pdel = sub.add_parser('delete')
    pdel.add_argument('key')
    sub.add_parser('clear')

    args = parser.parse_args()
    if args.cmd == 'view':
        s = memory.get_memory_summary(max_items=100)
        if not s:
            print('No memory stored')
        else:
            # pretty print underlying JSON
            try:
                import os, json
                p = os.path.join('assistant_memory.json')
                if os.path.exists(p):
                    print(json.dumps(json.load(open(p, 'r', encoding='utf-8')), indent=2, ensure_ascii=False))
                else:
                    print(s)
            except Exception:
                print(s)
    elif args.cmd == 'set':
        memory.update_memory(args.key, args.value)
        print('Set', args.key)
    elif args.cmd == 'delete':
        # manual delete via update with empty dict
        # load, remove, save
        import os, json
        p = 'assistant_memory.json'
        if os.path.exists(p):
            d = json.load(open(p, 'r', encoding='utf-8'))
        else:
            d = {}
        if args.key in d:
            d.pop(args.key)
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print('Deleted', args.key)
        else:
            print('Key not found')
    elif args.cmd == 'clear':
        import os, json
        p = 'assistant_memory.json'
        if os.path.exists(p):
            json.dump({}, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('Cleared memory')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
