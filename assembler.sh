#!/bin/bash

readarray assembly < asm

declare -A labels

out=""

function handle_jump() {

      args="$2"
      if [[ $args =~ ^[0-9]+$ ]]; then
        # Number
        # Should be in hex already
        num=$(printf "%04x" 0x$args)
        echo "NUM: " $num
        out+="\x"${num%[0-9a-f][0-9a-f]}"\x"${num%[0-9a-f][0-9a-f]}
      else
        # Label
        if [ ${labels[$args]+garbage} ]; then
          # Label was found
          out+="\x"${labels[$args]%[0-9a-f][0-9a-f]}"\x"${labels[$args]#[0-9a-f][0-9a-f]}
          echo "Jump to " ${labels[$args]}
          echo "\x"${labels[$args]%[0-9a-f][0-9a-f]}"\x"${labels[$args]#[0-9a-f][0-9a-f]}
        else
          if [ $1 -eq 1 ]; then
            # Placeholder
            out+="\x00\x00"
          else
            echo "THERE was a label error"
          fi
        fi
      fi
}

function handle_rm1 () {
  local args="$1"
  fword=${args%%,*}
  fchar="${fword:0:1}"

    case $fchar in
      r) echo "Reg"
        out+="\x00"
          reg=${fword#r}
        case $reg in
          a) out+="\x01";;
          b) out+="\x02";;
          c) out+="\x03";;
          d) out+="\x04";;
        esac
      ;;
      H) echo "Heap"
        out+="\x01"
        idx=${fword#H:}
        echo $idx
        out+="\x"${idx}
      ;;
      S) echo "Stack"
        out+="\x02"
        idx=${fword#S:}
        out+="\x"${idx}
      ;;
      [0-9]) echo "Imm"
        out+="\x03"
        out+="\x"$x
      ;;
      *) echo "Unhandled";;
    esac

}

function handle_rm2 () {
  local args="$1"
  fword=${args%%,*}
  sword=${args##*,}
  fchar="${fword:0:1}"
  schar="${sword:0:1}"

  declare -i count=0

  for x in $fchar $schar; do
    count+=1
    case $x in
      r) echo "Reg"
        out+="\x00"
        if [ $count == 1 ]; then
          reg=${fword#r}
        else
          reg=${sword#r}
        fi
        case $reg in
          a) out+="\x01";;
          b) out+="\x02";;
          c) out+="\x03";;
          d) out+="\x04";;
        esac
      ;;
      H) echo "Heap"
        out+="\x01"
        if [ $count == 1 ]; then
          idx=${fword#H:}
        else
          idx=${sword#H:}
        fi
        echo $idx
        out+="\x"${idx}
      ;;
      S) echo "Stack"
        out+="\x02"
        if [ $count == 1 ]; then
          idx=${fword#S:}
        else
          idx=${sword#S:}
        fi
        out+="\x"${idx}
      ;;
      [0-9]) echo "Imm"
        if [ $count == 1 ]; then
          echo "Cannot have immediate as dest"
          exit 1
        fi
        out+="\x03"
        out+="\x"$x
      ;;
      *) echo "Unhandled";;
    esac
  done

}
function assem() {
  out=""
  for line in "${assembly[@]}"; do

    line=${line//;*/}
    echo "_-" $line
    
    la=(${line})
    opt="${la[0]}"
    args="${la[1]}"
    if [ -z "$opt" ]; then
      continue
    elif [ ${opt:0:1} == ":" ]; then
      if [ $1 -eq 1 ]; then
        # Label
        labels[${opt##:}]=$(printf "%04x" $(echo -ne "${out}" | wc -c))
        echo "LABEL: $opt at ${labels[${opt##:}]}"
      fi
    elif [ $opt == "np" ]; then
      out+="\x00"
    elif [ $opt == "su" ]; then
      out+="\x06"
      handle_rm2 "$args"
    elif [ $opt == "ad" ]; then
      out+="\x04"
      handle_rm2 "$args"
    elif [ $opt == "mu" ]; then
      out+="\x03"
      handle_rm2 "$args"
    elif [ $opt == "di" ]; then
      out+="\x05"
      handle_rm2 "$args"
    elif [ $opt == "mv" ]; then
      out+="\x10"
      handle_rm2 "$args"
    elif [ $opt == "an" ]; then
      out+="\x14"
      handle_rm2 "$args"
    elif [ $opt == "nt" ]; then
      out+="\x28"
      handle_rm1 "$args"
    elif [ $opt == "ng" ]; then
      out+="\x29"
      handle_rm1 "$args"
    elif [ $opt == "pu" ]; then
      out+="\x16"
      handle_rm1 "$args"
    elif [ $opt == "po" ]; then
      out+="\x18"
      handle_rm1 "$args"
    elif [ $opt == "in" ]; then
      out+="\x20"
      handle_rm1 "$args"
    elif [ $opt == "dc" ]; then
      out+="\x22"
      handle_rm1 "$args"
    elif [ $opt == "cmp" ]; then
      out+="\x24"
      handle_rm2 "$args"
    elif [ $opt == "jz" ]; then
      out+="\x40"
      handle_jump $1 "$args"
    elif [ $opt == "jp" ]; then
      out+="\x42"
      handle_jump $1 "$args"
    elif [ $opt == "jn" ]; then
      out+="\x44"
      handle_jump $1 "$args"
    else
        echo "Unexpected opt" $opt
        exit 1
    fi	
  done
}

# First pass
assem 1
# Second pass
assem 2

echo -en "$out" > code
