import time
import cbcommon

if __name__ == "__main__":
    import sys
    import glob
    from threading import Thread

    disabled = []

    cb = cbcommon.CBDeploy()
    if "--all" in sys.argv:
        blueprints = glob.glob("blueprints/*.blueprint.json")
        blueprints = [b.split("/")[-1].split(".")[0] for b in blueprints]
        blueprints = [b for b in blueprints if b not in disabled]
    else:
        blueprints = sys.argv[1:]

    for i in range(0, len(blueprints)):
        print "Start integration test for blueprint " + blueprints[i]
        t = Thread(target=cb.wait_for_cluster, args=(blueprints[i],))
        t.start()
        t.join()
        time.sleep(20)