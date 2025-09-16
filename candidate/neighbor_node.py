#Author: 
#Date:
#This should be the only file you edit. You are free to look at other files for reference, but do not change them.
#Below are are two methods which you must implement: euclidean_dist_to_origin and nearest_neighbor as well as the main function beacon handling. 
#Helper Functions are allowed, but not required. You must not change the imports, the main function signature, or the return value of the main function.


"""
Neighbor Table

Listen on UDP 127.0.0.1:5005 for beacon messages:
  {"id":"veh_XXX","pos":[x,y],"speed":mps,"ts":epoch_ms}

Collect beacons for ~1 second starting from the *first* message.
Then print exactly ONE JSON line and exit:

{
  "topic": "/v2x/neighbor_summary",
  "count": <int>,
  "nearest": {"id": "...", "dist": <float>} OR null,
  "ts": <now_ms>
}

Constraints:
- Python 3 stdlib only.
- Ignore malformed messages; don’t crash.
- Do NOT listen to ticks (5006).
"""

import socket, json, time, math, sys
from typing import Dict, Any, Optional, Tuple

HOST = "127.0.0.1"
PORT_BEACON = 5005
COLLECT_WINDOW_MS = 1000  # ~1 second

def now_ms() -> int:
    return int(time.time() * 1000)

def euclidean_dist_to_origin(pos) -> float:
    # TODO: validate pos is [x,y] of numbers; compute distance
    # if not valid, return 0.0

    if not isinstance(pos, list) or len(pos) != 2: # Check that the pos is valid aka has two elements and is a list
        return float('inf') # If not valid return infinity so it is never the nearest neighbor
    x, y = pos
    if not (isinstance(x, (int, float)) and isinstance(y, (int, float))): # Check that both x and y are numbers
        return float('inf') # If not valid return infinity so it is never the nearest neighbor
    return float(math.hypot(x, y)) # Just return the hypotenuse which is the distance to the origin

def nearest_neighbor(neighbors: Dict[str, Dict[str, Any]]) -> Optional[Tuple[str, float]]:
    # neighbors[id] -> {"pos":[x,y], "speed": float, "last_ts": int}
    # TODO: iterate neighbors, compute min distance, return (id, dist) or None
    min_dist = float('inf')
    nearest_id = None
    for neighbor_id, data in neighbors.items(): 
        pos = data.get("pos") 
        dist = euclidean_dist_to_origin(pos) # Get the distance to the neighbor from the origin which is presumably the car
        if dist < min_dist:
            min_dist = dist
            nearest_id = neighbor_id
    if nearest_id is not None:
        return (nearest_id, min_dist) # Return the nearest neighbor id and its distance
    return None # If no neighbors return None

def main() -> int:
    neighbors: Dict[str, Dict[str, Any]] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT_BEACON))
    sock.settimeout(1.5) 

    first_ts: Optional[int] = None
    try:
        while True:
            try:
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                break  

            try:
                msg = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue  
            
            # Expect: {"id": "...", "pos":[x,y], "speed": float, "ts": int}
            # TODO: validate required keys/types defensively
            # If valid:
            #   neighbors[msg["id"]] = {"pos": msg["pos"], "speed": msg["speed"], "last_ts": msg["ts"]}
            #hint: beacon handling, check each message and store in neighbors, try to cover edge cases
            # try to avoid changing anything in the main function outside this TODO block

            if not isinstance(msg, dict): # Basically just check if msg, this is a bit redundant because we check if an exception is made but hey better safe than sorry you never know with python
                continue
            required_keys = {"id": str, "pos": list, "speed": (int, float), "ts": int}
            valid = True
            for key, expected_type in required_keys.items():
                if key not in msg or not isinstance(msg[key], expected_type): # Check if key exists and if it is the correct type
                    valid = False
                    break
            if not valid:
                continue # Skip to next message if the current msg is not valid
            neighbors[msg["id"]] = {"pos": msg["pos"], "speed": float(msg["speed"]), "last_ts": int(msg["ts"])}


            #END of TODO block
            now = now_ms()
            if first_ts is None:
                first_ts = now
            # stop after ~1 second from first message
            if first_ts is not None and (now - first_ts) >= COLLECT_WINDOW_MS:
                break

    finally:
        sock.close()

    # Build summary
    nn = nearest_neighbor(neighbors)
    summary = {
        "topic": "/v2x/neighbor_summary",
        "count": len(neighbors),
        "nearest": None if nn is None else {"id": nn[0], "dist": nn[1]},
        "ts": now_ms(),
    }
    print(json.dumps(summary), flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
