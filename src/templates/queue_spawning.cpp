#include "send_message.h"

typedef std::unordered_map<std::string, std::string> QueueSpawnParams;
void spawnQueues(std::vector<QueueSpawnParams> qp) {
	std::std::vector< std::unique_ptr<Queue> > queues(qp.size());
	size_t idx = 0;
	for (auto q : qp) {
		queues[idx] = std::move(createQueue())
	}
}